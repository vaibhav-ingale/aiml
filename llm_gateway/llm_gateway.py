import asyncio
import json
import logging
import os
import secrets
import time
from typing import Any, Dict, Optional

import httpx
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
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.0.0.100:1234")  # Default LM Studio URL, port 11434 for Ollama
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8008"))

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

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_all(
    request: Request,
    path: str,
    authorization: Optional[str] = Header(None)
):
    """Proxy all requests to LLM with API key authentication"""
    start_time = time.time()

    # Skip auth for health/info endpoints
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
    if is_models_endpoint:
        if "model" in request.query_params or (body and "model" in body):
            raise HTTPException(status_code=400, detail="Model parameter is not allowed for /models.")
    else:
        # Check model access
        if not model_name:
            raise HTTPException(status_code=400, detail="Model is required.")
        if not check_model_access(key_info, model_name):
            raise HTTPException(status_code=403, detail="Model is not allowed to use.")

    # Determine if this is a streaming request
    is_streaming = False
    if body:
        is_streaming = body.get("stream", False)

    # Proxy the request
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if is_streaming:
                # Handle streaming response
                async def stream_proxy():
                    input_tokens = 0
                    output_tokens = 0

                    try:
                        async with client.stream(
                            method=request.method,
                            url=f"{LLM_BASE_URL}/{path}",
                            json=body,
                            params=request.query_params,
                        ) as response:
                            async for chunk in response.aiter_bytes():
                                # Try to extract token counts from chunk
                                try:
                                    line = chunk.decode('utf-8').strip()
                                    if line.startswith('data: '):
                                        line = line[6:]
                                    if line and line != '[DONE]':
                                        data = json.loads(line)
                                        if "prompt_eval_count" in data:
                                            input_tokens = data["prompt_eval_count"]
                                        if "eval_count" in data:
                                            output_tokens = data["eval_count"]
                                except:
                                    pass

                                yield chunk

                        # Log usage after stream completes
                        if model_name:
                            response_time = time.time() - start_time
                            is_error = response.status_code >= 400
                            cost = 0.0 if is_error else calculate_cost(input_tokens, output_tokens, model_name)
                            error_message = None
                            if is_error:
                                error_message = f"Upstream status {response.status_code}"

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
                                error_message=error_message
                            )

                            if not is_error:
                                db.update_api_key_cost(key_info["id"], cost)
                    except Exception as e:
                        # Log error
                        if model_name:
                            response_time = time.time() - start_time
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
                                error_message=str(e)
                            )
                        raise

                return StreamingResponse(
                    stream_proxy(),
                    media_type="text/event-stream"
                )
            else:
                # Handle non-streaming response
                if body is not None:
                    response = await client.request(
                        method=request.method,
                        url=f"{LLM_BASE_URL}/{path}",
                        json=body,
                        params=request.query_params,
                    )
                elif raw_body:
                    response = await client.request(
                        method=request.method,
                        url=f"{LLM_BASE_URL}/{path}",
                        content=raw_body,
                        headers=dict(request.headers),
                        params=request.query_params,
                    )
                else:
                    response = await client.request(
                        method=request.method,
                        url=f"{LLM_BASE_URL}/{path}",
                        headers=dict(request.headers),
                        params=request.query_params,
                    )

                response_time = time.time() - start_time

                # Try to extract token counts from response
                input_tokens = 0
                output_tokens = 0
                try:
                    response_data = response.json()
                    print("Response data:", response_data)
                    if "usage" in response_data:
                        usage = response_data["usage"]
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)

                    print("Input tokens:", input_tokens, "Output tokens:", output_tokens)
                except:
                    pass

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
                        error_message=error_message
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
                error_message=str(e)
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
    uvicorn.run(app, host=GATEWAY_HOST, port=GATEWAY_PORT)
