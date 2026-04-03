import asyncio
import json
import logging
import os
import secrets
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import tiktoken
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEBUG_TOKEN_TRACKING = os.getenv("DEBUG_TOKEN_TRACKING", "False").lower() == "true"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.0.0.100:1234")  # Fallback for backward compatibility
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8008"))
GATEWAY_RELOAD = os.getenv("GATEWAY_RELOAD", "True").lower() == "true"

app = FastAPI(title="LLM Gateway API - Simple proxy that works!")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def extract_tool_info(response_data: Optional[Dict]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract tool call information from response data.
    Returns: (tool_name, tool_call_type, assistant_tool_calls_json)
    """
    tool_name = None
    tool_call_type = None
    assistant_tool_calls = None

    if not response_data:
        return tool_name, tool_call_type, assistant_tool_calls

    try:
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            if "message" in choice:
                message = choice["message"]

                # Check for tool_calls in the message
                if "tool_calls" in message and message["tool_calls"]:
                    tool_calls_list = message["tool_calls"]
                    assistant_tool_calls = json.dumps(tool_calls_list)

                    # Get the first tool call's name
                    first_tool = tool_calls_list[0]
                    if "function" in first_tool:
                        tool_name = first_tool["function"].get("name")
                        tool_call_type = "function"
                    elif "type" in first_tool:
                        tool_call_type = first_tool["type"]
                        if tool_call_type == "function" and "function" in first_tool:
                            tool_name = first_tool["function"].get("name")
    except Exception as e:
        logger.debug(f"Error extracting tool info: {e}")

    return tool_name, tool_call_type, assistant_tool_calls

def build_prompt_text(payload: Optional[Dict]) -> str:
    if not payload:
        return ""
    if "prompt" in payload and isinstance(payload["prompt"], str):
        return payload["prompt"]
    messages = payload.get("messages")
    if isinstance(messages, list):
        parts = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            content = message.get("content", "")
            if isinstance(content, str):
                parts.append(content)
        return "\n".join(parts)
    return ""

def debug_log(message: str, **kwargs):
    """Log debug message if DEBUG_TOKEN_TRACKING is enabled"""
    if DEBUG_TOKEN_TRACKING:
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        if extra_info:
            logger.info(f"[TOKEN_TRACKING] {message} | {extra_info}")
        else:
            logger.info(f"[TOKEN_TRACKING] {message}")

def calculate_cost(input_tokens: int, output_tokens: int, model_name: str) -> float:
    """Calculate cost based on token usage and model pricing"""
    pricing = db.get_model_pricing(model_name)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1000) * pricing["input_cost_per_1k"]
    output_cost = (output_tokens / 1000) * pricing["output_cost_per_1k"]
    return input_cost + output_cost

def verify_api_key(api_key: str) -> Optional[Dict]:
    """Verify API key and return key info"""
    if not api_key:
        return None

    key_info = db.get_api_key_info(api_key)
    if not key_info:
        return None

    # Check if cost limit exceeded
    if key_info["cost_limit"] > 0 and key_info["current_cost"] >= key_info["cost_limit"]:
        return None

    return key_info

def get_provider_for_model(model_name: str) -> Optional[Dict]:
    """
    Get provider configuration for a given model.
    Returns provider details with base_url and api_key for routing.
    """
    provider = db.get_provider_by_model(model_name)
    if not provider:
        logger.warning(f"No provider found for model: {model_name}")
        return None

    if not provider.get("is_active"):
        logger.warning(f"Provider {provider['provider_name']} is inactive for model: {model_name}")
        return None

    logger.info(f"Routing model '{model_name}' to provider: {provider['provider_name']} at {provider['base_url']}")
    return provider

def check_model_access(key_info: Dict, model_name: str) -> bool:
    """Check if API key has access to the requested model"""
    if not model_name:
        return True  # Allow if no model specified
    allowed_models = key_info.get("allowed_models", [])
    wildcard_entries = {"*", "* (All Models)"}
    has_wildcard = any(entry in wildcard_entries for entry in allowed_models)
    return model_name in allowed_models or has_wildcard

def filter_models_payload(payload: Any, allowed_models: list[str]) -> Any:
    """Filter model listings to only those allowed for the API key."""
    wildcard_entries = {"*", "* (All Models)"}
    if any(entry in wildcard_entries for entry in allowed_models):
        return payload

    def get_model_name(item: Any) -> Optional[str]:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            for key in ("model", "name", "id"):
                if key in item and isinstance(item[key], str):
                    return item[key]
        return None

    def filter_list(items: list[Any]) -> list[Any]:
        filtered = []
        for item in items:
            model_name = get_model_name(item)
            if model_name and model_name in allowed_models:
                filtered.append(item)
        return filtered

    if isinstance(payload, dict) and isinstance(payload.get("models"), list):
        payload["models"] = filter_list(payload["models"])
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        payload["data"] = filter_list(payload["data"])
        return payload
    if isinstance(payload, list):
        return filter_list(payload)
    return payload

@app.get("/")
async def root():
    return {"message": "LLM Gateway API - Simple Proxy", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None)):
    """List all models allowed for the authenticated API key"""
    # Extract API key
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")

    # Verify API key
    key_info = verify_api_key(api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    # Get allowed models for this API key
    allowed_models = key_info.get("allowed_models", [])
    wildcard_entries = {"*", "* (All Models)"}
    has_wildcard = any(entry in wildcard_entries for entry in allowed_models)

    # Get all models from database
    all_models = db.get_all_models()

    # Filter models based on API key permissions
    if has_wildcard:
        # Return all active models
        filtered_models = [m for m in all_models if m.get("is_active", True)]
    else:
        # Return only allowed models
        filtered_models = [m for m in all_models if m["model_name"] in allowed_models and m.get("is_active", True)]

    # Format response in OpenAI-compatible format
    model_list = {
        "object": "list",
        "data": [
            {
                "id": model["model_name"],
                "object": "model",
                "created": int(datetime.fromisoformat(model["created_at"]).timestamp()) if model.get("created_at") else int(time.time()),
                "owned_by": model.get("provider_name", "local"),
                "permission": [],
                "root": model["model_name"],
                "parent": None,
            }
            for model in filtered_models
        ]
    }

    return model_list

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_all(
    request: Request,
    path: str,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Proxy all requests to LLM with API key authentication and dynamic provider routing"""
    start_time = time.time()

    # Check if this is a custom endpoint request
    request_path = "/" + path if path and not path.startswith("/") else path
    custom_endpoint_path = request_path.split("/v1/")[0] if "/v1/" in request_path else None

    if custom_endpoint_path and custom_endpoint_path != "":
        # Try to get custom endpoint configuration
        custom_endpoint = db.get_custom_endpoint_by_path(custom_endpoint_path)

        if custom_endpoint:
            logger.info(f"Custom endpoint matched: {custom_endpoint_path}")

            # Use the custom endpoint's API key for authentication
            api_key = custom_endpoint["api_key"]
            key_info = verify_api_key(api_key)

            if not key_info:
                raise HTTPException(status_code=401, detail="Custom endpoint API key is invalid")

            # Get request body and inject/override the model
            body = None
            raw_body = await request.body()
            if raw_body:
                try:
                    body = json.loads(raw_body)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON in request body")
            else:
                body = {}

            # Override the model with primary model from custom endpoint
            model_name = custom_endpoint["primary_model"]
            body["model"] = model_name

            # Get provider for the primary model
            provider = get_provider_for_model(model_name)
            if not provider:
                # Try fallback model if primary model's provider is not available
                if custom_endpoint["fallback_model"]:
                    logger.warning(f"Primary model {model_name} provider not available, trying fallback")
                    model_name = custom_endpoint["fallback_model"]
                    body["model"] = model_name
                    provider = get_provider_for_model(model_name)

                    if not provider:
                        raise HTTPException(
                            status_code=503,
                            detail=f"Neither primary nor fallback model providers are available"
                        )
                else:
                    raise HTTPException(status_code=503, detail=f"Provider for model {model_name} is not available")

            # Extract the actual API path (everything after custom endpoint path)
            if "/v1/" in request_path:
                api_path = request_path.split("/v1/", 1)[1]
            else:
                raise HTTPException(status_code=400, detail="Invalid endpoint path format")

            # Route to the provider with the configured model
            target_url = f"{provider['base_url']}/v1/{api_path}"
            provider_api_key = provider.get("api_key")

            # Prepare headers
            proxy_headers = {"Content-Type": "application/json"}
            if provider_api_key:
                proxy_headers["Authorization"] = f"Bearer {provider_api_key}"

            logger.info(f"Routing custom endpoint to {target_url} with model {model_name}")

            # Generate trace_id for this request
            trace_id = str(uuid.uuid4())

            # Generate session_id if not provided in request
            # Format: endpoint-name-with-dashes-epochmillis
            if not x_session_id:
                endpoint_name = custom_endpoint["endpoint_name"].replace(" ", "-").lower()
                epoch_millis = int(time.time() * 1000)
                x_session_id = f"{endpoint_name}-{epoch_millis}"
                logger.debug(f"Auto-generated session_id: {x_session_id}")

            # Make the request with fallback support
            primary_model_name = model_name
            fallback_attempted = False

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=proxy_headers,
                        json=body,
                        params=request.query_params,
                    )

                    # Calculate response time
                    response_time = time.time() - start_time

                    # Parse response to extract tokens
                    input_tokens = 0
                    output_tokens = 0
                    response_data = None

                    try:
                        response_data = response.json()
                        if "usage" in response_data:
                            input_tokens = response_data["usage"].get("prompt_tokens", 0)
                            output_tokens = response_data["usage"].get("completion_tokens", 0)
                        else:
                            # Estimate tokens if not provided
                            prompt_text = build_prompt_text(body)
                            input_tokens = count_tokens(prompt_text) if prompt_text else 0

                            # Try to extract output from response
                            if "choices" in response_data and len(response_data["choices"]) > 0:
                                choice = response_data["choices"][0]
                                if "message" in choice and "content" in choice["message"]:
                                    output_text = choice["message"]["content"]
                                    output_tokens = count_tokens(output_text) if output_text else 0
                    except Exception as e:
                        logger.warning(f"Failed to parse response for token counting: {e}")
                        prompt_text = build_prompt_text(body)
                        input_tokens = count_tokens(prompt_text) if prompt_text else 0

                    # Calculate cost
                    is_error = response.status_code >= 400
                    cost = 0.0 if is_error else calculate_cost(input_tokens, output_tokens, model_name)

                    # Extract messages for logging
                    messages = body.get("messages", []) if body else []
                    system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                    user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)
                    assistant_msg = None
                    assistant_tool_calls = None
                    tool_name = None
                    tool_call_type = None

                    if response_data:
                        # Extract assistant message
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            choice = response_data["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                assistant_msg = choice["message"]["content"]

                        # Extract tool info
                        tool_name, tool_call_type, assistant_tool_calls = extract_tool_info(response_data)

                    # Log usage
                    db.log_usage(
                        api_key_id=key_info["id"],
                        user_id=key_info["user_id"],
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        response_time=response_time,
                        cost=cost,
                        endpoint=custom_endpoint_path,
                        status="error" if is_error else "success",
                        error_message=response.text if is_error else None,
                        trace_id=trace_id,
                        session_id=x_session_id,
                        request_payload=json.dumps(body) if body else None,
                        response_payload=response.text if not is_error else None,
                        system_message=system_msg,
                        user_message=user_msg,
                        assistant_message=assistant_msg,
                        assistant_tool_calls=assistant_tool_calls,
                        stream_setting="false",
                        temperature=body.get("temperature") if body else None,
                        tool_name=tool_name,
                        tool_call_type=tool_call_type,
                    )

                    # Update API key cost
                    if cost > 0:
                        db.update_api_key_cost(key_info["id"], cost)

                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
            except Exception as e:
                logger.error(f"Primary model {primary_model_name} request failed: {str(e)}")

                # Try fallback model if available and not already attempted
                if custom_endpoint["fallback_model"] and not fallback_attempted:
                    fallback_attempted = True
                    fallback_model_name = custom_endpoint["fallback_model"]
                    logger.warning(f"Trying fallback model {fallback_model_name}")

                    # Update body with fallback model
                    body["model"] = fallback_model_name

                    # Get provider for fallback model
                    fallback_provider = get_provider_for_model(fallback_model_name)
                    if not fallback_provider:
                        logger.error(f"Fallback model {fallback_model_name} provider not available")
                        raise HTTPException(status_code=503, detail=f"Both primary and fallback providers are unavailable")

                    # Build fallback URL
                    fallback_target_url = f"{fallback_provider['base_url']}/v1/{api_path}"
                    fallback_api_key = fallback_provider.get("api_key")

                    # Prepare fallback headers
                    fallback_headers = {"Content-Type": "application/json"}
                    if fallback_api_key:
                        fallback_headers["Authorization"] = f"Bearer {fallback_api_key}"

                    try:
                        async with httpx.AsyncClient(timeout=10.0) as fallback_client:
                            fallback_response = await fallback_client.request(
                                method=request.method,
                                url=fallback_target_url,
                                headers=fallback_headers,
                                json=body,
                                params=request.query_params,
                            )

                            logger.info(f"Fallback model {fallback_model_name} succeeded")

                            # Calculate response time for fallback
                            fallback_response_time = time.time() - start_time

                            # Parse fallback response to extract tokens
                            fallback_input_tokens = 0
                            fallback_output_tokens = 0
                            fallback_response_data = None

                            try:
                                fallback_response_data = fallback_response.json()
                                if "usage" in fallback_response_data:
                                    fallback_input_tokens = fallback_response_data["usage"].get("prompt_tokens", 0)
                                    fallback_output_tokens = fallback_response_data["usage"].get("completion_tokens", 0)
                                else:
                                    # Estimate tokens if not provided
                                    prompt_text = build_prompt_text(body)
                                    fallback_input_tokens = count_tokens(prompt_text) if prompt_text else 0

                                    # Try to extract output from response
                                    if "choices" in fallback_response_data and len(fallback_response_data["choices"]) > 0:
                                        choice = fallback_response_data["choices"][0]
                                        if "message" in choice and "content" in choice["message"]:
                                            output_text = choice["message"]["content"]
                                            fallback_output_tokens = count_tokens(output_text) if output_text else 0
                            except Exception as e:
                                logger.warning(f"Failed to parse fallback response for token counting: {e}")
                                prompt_text = build_prompt_text(body)
                                fallback_input_tokens = count_tokens(prompt_text) if prompt_text else 0

                            # Calculate cost for fallback
                            fallback_is_error = fallback_response.status_code >= 400
                            fallback_cost = 0.0 if fallback_is_error else calculate_cost(fallback_input_tokens, fallback_output_tokens, fallback_model_name)

                            # Extract messages for logging
                            messages = body.get("messages", []) if body else []
                            system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                            user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)
                            assistant_msg = None
                            assistant_tool_calls = None
                            tool_name = None
                            tool_call_type = None

                            if fallback_response_data:
                                # Extract assistant message
                                if "choices" in fallback_response_data and len(fallback_response_data["choices"]) > 0:
                                    choice = fallback_response_data["choices"][0]
                                    if "message" in choice and "content" in choice["message"]:
                                        assistant_msg = choice["message"]["content"]

                                # Extract tool info
                                tool_name, tool_call_type, assistant_tool_calls = extract_tool_info(fallback_response_data)

                            # Log usage for fallback
                            db.log_usage(
                                api_key_id=key_info["id"],
                                user_id=key_info["user_id"],
                                model_name=fallback_model_name,
                                input_tokens=fallback_input_tokens,
                                output_tokens=fallback_output_tokens,
                                response_time=fallback_response_time,
                                cost=fallback_cost,
                                endpoint=custom_endpoint_path,
                                status="error" if fallback_is_error else "success",
                                error_message=fallback_response.text if fallback_is_error else None,
                                trace_id=trace_id,
                                session_id=x_session_id,
                                request_payload=json.dumps(body) if body else None,
                                response_payload=fallback_response.text if not fallback_is_error else None,
                                system_message=system_msg,
                                user_message=user_msg,
                                assistant_message=assistant_msg,
                                assistant_tool_calls=assistant_tool_calls,
                                stream_setting="false",
                                temperature=body.get("temperature") if body else None,
                                tool_name=tool_name,
                                tool_call_type=tool_call_type,
                            )

                            # Update API key cost for fallback
                            if fallback_cost > 0:
                                db.update_api_key_cost(key_info["id"], fallback_cost)

                            return Response(
                                content=fallback_response.content,
                                status_code=fallback_response.status_code,
                                headers=dict(fallback_response.headers)
                            )
                    except Exception as fallback_error:
                        logger.error(f"Fallback model {fallback_model_name} also failed: {str(fallback_error)}")

                        # Log the fallback failure
                        fallback_response_time = time.time() - start_time
                        messages = body.get("messages", []) if body else []
                        system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                        user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

                        db.log_usage(
                            api_key_id=key_info["id"],
                            user_id=key_info["user_id"],
                            model_name=fallback_model_name,
                            input_tokens=0,
                            output_tokens=0,
                            response_time=fallback_response_time,
                            cost=0.0,
                            endpoint=custom_endpoint_path,
                            status="error",
                            error_message=f"Fallback failed: {str(fallback_error)}",
                            trace_id=trace_id,
                            session_id=x_session_id,
                            request_payload=json.dumps(body) if body else None,
                            system_message=system_msg,
                            user_message=user_msg,
                            stream_setting="false",
                            temperature=body.get("temperature") if body else None,
                        )

                        raise HTTPException(
                            status_code=503,
                            detail=f"Both primary model ({primary_model_name}) and fallback model ({fallback_model_name}) failed"
                        )
                else:
                    # No fallback available - log the error
                    error_response_time = time.time() - start_time
                    messages = body.get("messages", []) if body else []
                    system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                    user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

                    db.log_usage(
                        api_key_id=key_info["id"],
                        user_id=key_info["user_id"],
                        model_name=primary_model_name,
                        input_tokens=0,
                        output_tokens=0,
                        response_time=error_response_time,
                        cost=0.0,
                        endpoint=custom_endpoint_path,
                        status="error",
                        error_message=str(e),
                        trace_id=trace_id,
                        session_id=x_session_id,
                        request_payload=json.dumps(body) if body else None,
                        system_message=system_msg,
                        user_message=user_msg,
                        stream_setting="false",
                        temperature=body.get("temperature") if body else None,
                    )

                    raise HTTPException(status_code=503, detail=f"Request failed: {str(e)}")

    # Skip auth for health/info endpoints (use fallback URL for backward compatibility)
    if path in ["", "health", "version"]:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{LLM_BASE_URL}/{path}",
                headers=dict(request.headers),
                params=request.query_params,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    # Extract API key
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")

    # Verify API key
    key_info = verify_api_key(api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    # Get request body
    body = None
    raw_body = await request.body()
    model_name = None
    if raw_body:
        try:
            body = json.loads(raw_body)
            model_name = body.get("model", "")
        except json.JSONDecodeError:
            body = None

    is_models_endpoint = path.endswith("models")

    # Determine target URL (provider-based or fallback)
    target_base_url = LLM_BASE_URL  # Default fallback
    provider_api_key = None

    if is_models_endpoint:
        if "model" in request.query_params or (body and "model" in body):
            raise HTTPException(status_code=400, detail="Model parameter is not allowed for /models.")
    else:
        # Check model access
        if not model_name:
            raise HTTPException(status_code=400, detail="Model is required.")
        if not check_model_access(key_info, model_name):
            raise HTTPException(status_code=403, detail="Model is not allowed to use.")

        # Get provider for this model (dynamic routing)
        provider = get_provider_for_model(model_name)
        if provider:
            target_base_url = provider["base_url"]
            provider_api_key = provider.get("api_key")
            logger.info(f"Using provider {provider['provider_name']} at {target_base_url} for model {model_name}")
        else:
            # Fallback to default LLM_BASE_URL for backward compatibility
            logger.warning(f"No provider configured for model {model_name}, using fallback URL: {target_base_url}")

    # Determine if this is a streaming request
    is_streaming = False
    if body:
        is_streaming = body.get("stream", False)

    # Generate trace_id for this request
    trace_id = str(uuid.uuid4())
    request_time = datetime.now().isoformat()

    # Proxy the request
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if is_streaming:
                # Handle streaming response
                async def stream_proxy():
                    prompt_text = build_prompt_text(body)
                    input_tokens = count_tokens(prompt_text) if prompt_text else 0
                    output_text = ""
                    output_tokens = 0
                    response_data = None

                    try:
                        # Prepare headers with provider API key if available
                        stream_headers = {"Content-Type": "application/json"}
                        if provider_api_key:
                            stream_headers["Authorization"] = f"Bearer {provider_api_key}"

                        async with httpx.AsyncClient(timeout=300.0) as stream_client:
                            async with stream_client.stream(
                                method=request.method,
                                url=f"{target_base_url}/{path}",
                                json=body,
                                params=request.query_params,
                                headers=stream_headers,
                            ) as response:
                                async for chunk in response.aiter_bytes():
                                    # Try to extract token counts from chunk
                                    try:
                                        line = chunk.decode("utf-8").strip()
                                        if line.startswith("data: "):
                                            line = line[6:]
                                        if line and line != "[DONE]":
                                            data = json.loads(line)
                                            if "prompt_eval_count" in data:
                                                input_tokens = data["prompt_eval_count"]
                                            if "eval_count" in data:
                                                output_tokens = data["eval_count"]
                                            choices = data.get("choices")
                                            if isinstance(choices, list) and choices:
                                                delta = choices[0].get("delta", {})
                                                if isinstance(delta, dict):
                                                    content = delta.get("content", "")
                                                    if content:
                                                        output_text += content
                                    except:
                                        pass

                                    yield chunk

                        if output_text and output_tokens == 0:
                            output_tokens = count_tokens(output_text)
                        total_tokens = input_tokens + output_tokens
                        debug_log(
                            "streaming tokens",
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens
                        )

                        # Log usage after stream completes
                        if model_name:
                            response_time = time.time() - start_time
                            is_error = response.status_code >= 400
                            cost = 0.0 if is_error else calculate_cost(input_tokens, output_tokens, model_name)
                            error_message = None
                            if is_error:
                                error_message = f"Upstream status {response.status_code}"

                            # Extract messages from request
                            messages = body.get("messages", []) if body else []
                            system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                            user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

                            # Note: Streaming responses don't typically include tool calls in chunks
                            # Tool information would need to be extracted from accumulated response
                            db.log_usage(
                                api_key_id=key_info["id"],
                                user_id=key_info["user_id"],
                                model_name=model_name,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                response_time=response_time,
                                cost=cost,
                                endpoint=f"/{path}",
                                status="error" if is_error else "success",
                                error_message=error_message,
                                trace_id=trace_id,
                                session_id=x_session_id,
                                request_payload=json.dumps(body) if body else None,
                                response_payload=json.dumps({"content": output_text}) if output_text else None,
                                system_message=system_msg,
                                user_message=user_msg,
                                assistant_message=output_text if output_text else None,
                                stream_setting="true" if is_streaming else "false",
                                temperature=body.get("temperature") if body else None,
                                tool_name=None,
                                tool_call_type=None,
                                request_time=request_time
                            )

                            if not is_error:
                                db.update_api_key_cost(key_info["id"], cost)
                    except Exception as e:
                        # Log error
                        if model_name:
                            response_time = time.time() - start_time

                            # Extract messages from request
                            messages = body.get("messages", []) if body else []
                            system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                            user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

                            db.log_usage(
                                api_key_id=key_info["id"],
                                user_id=key_info["user_id"],
                                model_name=model_name,
                                input_tokens=0,
                                output_tokens=0,
                                response_time=response_time,
                                cost=0.0,
                                endpoint=f"/{path}",
                                status="error",
                                error_message=str(e),
                                trace_id=trace_id,
                                session_id=x_session_id,
                                request_payload=json.dumps(body) if body else None,
                                system_message=system_msg,
                                user_message=user_msg,
                                stream_setting="true" if is_streaming else "false",
                                temperature=body.get("temperature") if body else None,
                                tool_name=None,
                                tool_call_type=None,
                                request_time=request_time
                            )
                        raise

                return StreamingResponse(
                    stream_proxy(),
                    media_type="text/event-stream"
                )
            else:
                # Handle non-streaming response
                # Prepare headers with provider API key if available
                request_headers = {"Content-Type": "application/json"}
                if provider_api_key:
                    request_headers["Authorization"] = f"Bearer {provider_api_key}"

                if body is not None:
                    response = await client.request(
                        method=request.method,
                        url=f"{target_base_url}/{path}",
                        json=body,
                        params=request.query_params,
                        headers=request_headers,
                    )
                elif raw_body:
                    response = await client.request(
                        method=request.method,
                        url=f"{target_base_url}/{path}",
                        content=raw_body,
                        headers={**dict(request.headers), **request_headers},
                        params=request.query_params,
                    )
                else:
                    response = await client.request(
                        method=request.method,
                        url=f"{target_base_url}/{path}",
                        headers={**dict(request.headers), **request_headers},
                        params=request.query_params,
                    )

                response_time = time.time() - start_time

                # Try to extract token counts from response
                input_tokens = 0
                output_tokens = 0
                response_data = None
                assistant_msg = None
                tool_name = None
                tool_call_type = None
                assistant_tool_calls = None
                try:
                    response_data = response.json()
                    if "usage" in response_data:
                        usage = response_data["usage"]
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)
                    # Extract assistant message
                    if "choices" in response_data and response_data["choices"]:
                        choice = response_data["choices"][0]
                        if "message" in choice:
                            assistant_msg = choice["message"].get("content")
                    # Extract tool information
                    tool_name, tool_call_type, assistant_tool_calls = extract_tool_info(response_data)
                except:
                    pass
                total_tokens = input_tokens + output_tokens
                if input_tokens or output_tokens:
                    debug_log(
                        "response tokens",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens
                    )

                # Log usage
                if model_name:
                    is_error = response.status_code >= 400
                    cost = 0.0 if is_error else calculate_cost(input_tokens, output_tokens, model_name)
                    error_message = None
                    if is_error:
                        try:
                            error_message = response.text
                        except Exception:
                            error_message = f"Upstream status {response.status_code}"

                    # Extract messages from request
                    messages = body.get("messages", []) if body else []
                    system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
                    user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

                    db.log_usage(
                        api_key_id=key_info["id"],
                        user_id=key_info["user_id"],
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        response_time=response_time,
                        cost=cost,
                        endpoint=f"/{path}",
                        status="error" if is_error else "success",
                        error_message=error_message,
                        trace_id=trace_id,
                        session_id=x_session_id,
                        request_payload=json.dumps(body) if body else None,
                        response_payload=json.dumps(response_data) if response_data else None,
                        system_message=system_msg,
                        user_message=user_msg,
                        assistant_message=assistant_msg,
                        assistant_tool_calls=assistant_tool_calls,
                        stream_setting="false",
                        temperature=body.get("temperature") if body else None,
                        tool_name=tool_name,
                        tool_call_type=tool_call_type,
                        request_time=request_time
                    )

                    if not is_error:
                        db.update_api_key_cost(key_info["id"], cost)

                if is_models_endpoint:
                    try:
                        response_data = response.json()
                        filtered = filter_models_payload(
                            response_data,
                            key_info.get("allowed_models", [])
                        )
                        return Response(
                            content=json.dumps(filtered),
                            status_code=response.status_code,
                            headers={"Content-Type": "application/json"}
                        )
                    except Exception:
                        pass

                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

    except Exception as e:
        response_time = time.time() - start_time

        # Log error
        if model_name:
            # Extract messages from request
            messages = body.get("messages", []) if body else []
            system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)
            user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), None)

            db.log_usage(
                api_key_id=key_info["id"],
                user_id=key_info["user_id"],
                model_name=model_name,
                input_tokens=0,
                output_tokens=0,
                response_time=response_time,
                cost=0.0,
                endpoint=f"/{path}",
                status="error",
                error_message=str(e),
                trace_id=trace_id,
                session_id=x_session_id,
                request_payload=json.dumps(body) if body else None,
                system_message=system_msg,
                user_message=user_msg,
                stream_setting="true" if is_streaming else "false",
                temperature=body.get("temperature") if body else None,
                tool_name=None,
                tool_call_type=None,
                request_time=request_time
            )

        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")

# Admin endpoints (these would typically require admin authentication)
@app.post("/admin/users")
async def create_user(username: str):
    """Create a new user"""
    user_id = db.create_user(username)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"user_id": user_id, "username": username}

@app.post("/admin/api-keys")
async def create_api_key_endpoint(
    user_id: int,
    allowed_models: list[str],
    cost_limit: float = 0.0
):
    """Generate a new API key for a user"""
    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate API key
    api_key = f"llmgw-{secrets.token_urlsafe(32)}"

    # Create API key in database
    api_key_id = db.create_api_key(user_id, api_key, allowed_models, cost_limit)

    return {
        "api_key_id": api_key_id,
        "api_key": api_key,
        "user_id": user_id,
        "allowed_models": allowed_models,
        "cost_limit": cost_limit
    }

@app.post("/admin/models")
async def add_model_pricing(
    model_name: str,
    input_cost_per_1k: float,
    output_cost_per_1k: float
):
    """Add or update model pricing"""
    model_id = db.add_model(model_name, input_cost_per_1k, output_cost_per_1k)
    return {
        "model_id": model_id,
        "model_name": model_name,
        "input_cost_per_1k": input_cost_per_1k,
        "output_cost_per_1k": output_cost_per_1k
    }

if __name__ == "__main__":
    import uvicorn

    gateway_module = os.path.splitext(os.path.basename(__file__))[0]
    uvicorn.run(
        f"{gateway_module}:app",
        host=GATEWAY_HOST,
        port=GATEWAY_PORT,
        reload=GATEWAY_RELOAD,
        reload_dirs=[os.path.dirname(os.path.abspath(__file__))],
    )
