import { resolve } from "path";
import { Database } from "./db";

const dbPath = process.env.DB_PATH || resolve(import.meta.dir, "../../llm_gateway.db");
const db = new Database(dbPath);
const publicDir = resolve(import.meta.dir, "../public");

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function errorResponse(message: string, status = 400) {
  return new Response(message, { status });
}

function parseId(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  return Number(parts[parts.length - 1]);
}

async function serveFile(pathname: string) {
  const decoded = decodeURIComponent(pathname);
  const filePath = resolve(publicDir, "." + decoded);
  if (!filePath.startsWith(publicDir)) {
    return errorResponse("Forbidden", 403);
  }

  const file = Bun.file(filePath);
  const exists = await file.exists();
  if (!exists && decoded !== "/" && !decoded.includes(".")) {
    return new Response(Bun.file(resolve(publicDir, "index.html")));
  }

  if (!exists) {
    return errorResponse("Not found", 404);
  }

  return new Response(file);
}

const server = Bun.serve({
  port: Number(process.env.DASHBOARD_PORT || 8010),
  async fetch(req) {
    const url = new URL(req.url);
    const { pathname } = url;

    if (pathname.startsWith("/api/")) {
      try {
        if (pathname === "/api/summary" && req.method === "GET") {
          const userId = url.searchParams.get("user_id");
          return jsonResponse(db.getSummaryStats(userId ? Number(userId) : null));
        }

        if (pathname === "/api/usage" && req.method === "GET") {
          const days = Number(url.searchParams.get("days") || 30);
          const userId = url.searchParams.get("user_id");
          return jsonResponse(db.getUsageStats(userId ? Number(userId) : null, days));
        }

        if (pathname === "/api/users" && req.method === "GET") {
          return jsonResponse(db.getAllUsers());
        }

        if (pathname === "/api/users/with-stats" && req.method === "GET") {
          const users = db.getAllUsers();
          const payload = users.map((user) => {
            const summary = db.getSummaryStats(user.id);
            const apiKeys = db.getUserApiKeys(user.id);
            return {
              ...user,
              total_requests: summary.total_requests,
              total_cost: summary.total_cost,
              api_keys_count: apiKeys.length,
            };
          });
          return jsonResponse(payload);
        }

        if (pathname.startsWith("/api/users/") && pathname.endsWith("/api-keys") && req.method === "GET") {
          const userId = parseId(pathname.replace("/api-keys", ""));
          return jsonResponse(db.getUserApiKeys(userId));
        }

        if (pathname.startsWith("/api/users/") && req.method === "GET") {
          const userId = parseId(pathname);
          const user = db.getUser(userId);
          if (!user) return errorResponse("User not found", 404);
          return jsonResponse(user);
        }

        if (pathname === "/api/users" && req.method === "POST") {
          const body = await req.json();
          if (!body.username) return errorResponse("Username required", 400);
          const userId = db.createUser(body.username);
          if (!userId) return errorResponse("Username already exists", 409);
          return jsonResponse({ id: userId }, 201);
        }

        if (pathname.startsWith("/api/users/") && req.method === "DELETE") {
          const userId = parseId(pathname);
          db.deleteUser(userId);
          return new Response(null, { status: 204 });
        }

        if (pathname === "/api/api-keys" && req.method === "GET") {
          return jsonResponse(db.getAllApiKeys());
        }

        if (pathname === "/api/api-keys" && req.method === "POST") {
          const body = await req.json();
          const userId = Number(body.user_id);
          if (!userId) return errorResponse("User ID required", 400);
          const allowed = Array.isArray(body.allowed_models) ? body.allowed_models : [];
          const costLimit = Number(body.cost_limit || 0);
          const token = crypto.getRandomValues(new Uint8Array(24));
          const apiKey = `llmgw-${Buffer.from(token).toString("base64url")}`;
          const apiKeyId = db.createApiKey(userId, apiKey, allowed, costLimit);
          return jsonResponse({ id: apiKeyId, api_key: apiKey }, 201);
        }

        if (pathname.startsWith("/api/api-keys/") && req.method === "PATCH") {
          const apiKeyId = parseId(pathname);
          const body = await req.json();
          if (typeof body.is_active !== "boolean") return errorResponse("is_active required", 400);
          const apiKey = db.getApiKeyById(apiKeyId);
          if (!apiKey) return errorResponse("API key not found", 404);
          if (body.is_active && !apiKey.is_active) {
            return errorResponse("Disabled API keys cannot be re-enabled", 400);
          }
          db.updateApiKeyStatus(apiKeyId, body.is_active);
          return new Response(null, { status: 204 });
        }

        if (pathname.startsWith("/api/api-keys/") && req.method === "DELETE") {
          const apiKeyId = parseId(pathname);
          db.deleteApiKey(apiKeyId);
          return new Response(null, { status: 204 });
        }

        if (pathname === "/api/models" && req.method === "GET") {
          return jsonResponse(db.getAllModels());
        }

        if (pathname === "/api/models" && req.method === "POST") {
          const body = await req.json();
          if (!body.model_name) return errorResponse("Model name required", 400);
          const modelId = db.addModel(
            body.model_name,
            Number(body.input_cost_per_1k || 0),
            Number(body.output_cost_per_1k || 0)
          );
          return jsonResponse({ id: modelId }, 201);
        }

        if (pathname.startsWith("/api/models/") && req.method === "DELETE") {
          const modelId = parseId(pathname);
          db.deleteModel(modelId);
          return new Response(null, { status: 204 });
        }

        if (pathname === "/api/traces" && req.method === "GET") {
          const limit = Number(url.searchParams.get("limit") || 100);
          const offset = Number(url.searchParams.get("offset") || 0);
          const userId = url.searchParams.get("user_id");
          const sessionId = url.searchParams.get("session_id");
          const traces = db.getTraces(limit, offset, userId ? Number(userId) : null, sessionId);
          const total = db.getTraceCount(userId ? Number(userId) : null, sessionId);
          return jsonResponse({ traces, total, limit, offset });
        }

        if (pathname === "/api/traces/sessions" && req.method === "GET") {
          const sessions = db.getUniqueSessions();
          return jsonResponse(sessions);
        }

        if (pathname === "/api/traces/clear" && req.method === "DELETE") {
          db.clearAllTraces();
          return jsonResponse({ success: true, message: "All traces cleared" });
        }

        if (pathname === "/api/traces/delete-multiple" && req.method === "DELETE") {
          const body = await req.json();
          if (!body.traceIds || !Array.isArray(body.traceIds)) {
            return errorResponse("traceIds array required", 400);
          }
          const deletedCount = db.deleteTraces(body.traceIds);
          return jsonResponse({ success: true, deletedCount });
        }

        if (pathname.startsWith("/api/traces/") && req.method === "GET") {
          const traceId = pathname.split("/").filter(Boolean).pop();
          if (!traceId) return errorResponse("Trace ID required", 400);
          const trace = db.getTraceById(traceId);
          if (!trace) return errorResponse("Trace not found", 404);
          return jsonResponse(trace);
        }

        // LLM Providers endpoints
        if (pathname === "/api/providers" && req.method === "GET") {
          return jsonResponse(db.getAllProviders());
        }

        if (pathname === "/api/providers" && req.method === "POST") {
          const body = await req.json();
          if (!body.provider_name) return errorResponse("Provider name required", 400);
          if (!body.base_url) return errorResponse("Base URL required", 400);

          try {
            const providerId = db.createProvider(
              body.provider_name,
              body.base_url,
              body.api_key || null,
              body.allowed_models || []
            );
            return jsonResponse({ id: providerId }, 201);
          } catch (error) {
            return errorResponse("Provider name already exists", 409);
          }
        }

        if (pathname.startsWith("/api/providers/") && pathname.endsWith("/health") && req.method === "GET") {
          const providerId = parseId(pathname.replace("/health", ""));
          const provider = db.getProvider(providerId);
          if (!provider) return errorResponse("Provider not found", 404);

          try {
            // Test connection to provider
            const healthUrl = `${provider.base_url}/v1/models`;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const healthResponse = await fetch(healthUrl, {
              method: "GET",
              signal: controller.signal,
              headers: provider.api_key
                ? { Authorization: `Bearer ${provider.api_key}` }
                : {},
            });

            clearTimeout(timeoutId);

            const status = healthResponse.ok ? "online" : "offline";
            db.updateProviderHealth(providerId, status);

            return jsonResponse({
              status,
              provider_id: providerId,
              provider_name: provider.provider_name,
            });
          } catch (error) {
            db.updateProviderHealth(providerId, "offline");
            return jsonResponse({
              status: "offline",
              provider_id: providerId,
              provider_name: provider.provider_name,
              error: error instanceof Error ? error.message : "Connection failed",
            });
          }
        }

        if (pathname.startsWith("/api/providers/") && pathname.endsWith("/models") && req.method === "GET") {
          const providerId = parseId(pathname.replace("/models", ""));
          const provider = db.getProvider(providerId);
          if (!provider) return errorResponse("Provider not found", 404);

          try {
            // Fetch models from provider
            const modelsUrl = `${provider.base_url}/v1/models`;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const modelsResponse = await fetch(modelsUrl, {
              method: "GET",
              signal: controller.signal,
              headers: provider.api_key
                ? { Authorization: `Bearer ${provider.api_key}` }
                : {},
            });

            clearTimeout(timeoutId);

            if (!modelsResponse.ok) {
              throw new Error(`HTTP ${modelsResponse.status}`);
            }

            const data = await modelsResponse.json();
            const models = data.data || [];

            return jsonResponse({
              provider_id: providerId,
              provider_name: provider.provider_name,
              models: models.map((m: any) => ({
                id: m.id,
                object: m.object,
                owned_by: m.owned_by,
              })),
            });
          } catch (error) {
            return errorResponse(
              error instanceof Error ? error.message : "Failed to fetch models",
              500
            );
          }
        }

        if (pathname.startsWith("/api/providers/") && pathname.endsWith("/refresh-models") && req.method === "POST") {
          const providerId = parseId(pathname.replace("/refresh-models", ""));
          const provider = db.getProvider(providerId);
          if (!provider) return errorResponse("Provider not found", 404);

          try {
            // Fetch models from provider
            const modelsUrl = `${provider.base_url}/v1/models`;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const modelsResponse = await fetch(modelsUrl, {
              method: "GET",
              signal: controller.signal,
              headers: provider.api_key
                ? { Authorization: `Bearer ${provider.api_key}` }
                : {},
            });

            clearTimeout(timeoutId);

            if (!modelsResponse.ok) {
              throw new Error(`HTTP ${modelsResponse.status}`);
            }

            const data = await modelsResponse.json();
            const models = data.data || [];

            // Save models to database (only new ones)
            let addedCount = 0;
            for (const model of models) {
              const result = db.addModelIfNotExists(
                model.id,
                0.0, // Default input cost
                0.0, // Default output cost
                provider.provider_name
              );
              if (result !== null) {
                addedCount++;
              }
            }

            return jsonResponse({
              success: true,
              provider_id: providerId,
              provider_name: provider.provider_name,
              models_count: models.length,
              added_count: addedCount,
            });
          } catch (error) {
            return errorResponse(
              error instanceof Error ? error.message : "Failed to refresh models",
              500
            );
          }
        }

        if (pathname.startsWith("/api/providers/") && req.method === "GET") {
          const providerId = parseId(pathname);
          const provider = db.getProvider(providerId);
          if (!provider) return errorResponse("Provider not found", 404);
          return jsonResponse(provider);
        }

        if (pathname.startsWith("/api/providers/") && req.method === "PATCH") {
          const providerId = parseId(pathname);
          const body = await req.json();

          const provider = db.getProvider(providerId);
          if (!provider) return errorResponse("Provider not found", 404);

          db.updateProvider(providerId, body);
          return new Response(null, { status: 204 });
        }

        if (pathname.startsWith("/api/providers/") && req.method === "DELETE") {
          const providerId = parseId(pathname);
          db.deleteProvider(providerId);
          return new Response(null, { status: 204 });
        }

        // Custom Endpoints Management
        if (pathname === "/api/custom-endpoints" && req.method === "GET") {
          return jsonResponse(db.getAllCustomEndpoints());
        }

        if (pathname === "/api/custom-endpoints" && req.method === "POST") {
          const body = await req.json();
          if (!body.endpoint_name) return errorResponse("Endpoint name required", 400);
          if (!body.endpoint_path) return errorResponse("Endpoint path required", 400);
          if (!body.api_key) return errorResponse("API key required", 400);
          if (!body.primary_model) return errorResponse("Primary model required", 400);

          // Validate endpoint path format
          if (!body.endpoint_path.startsWith("/")) {
            return errorResponse("Endpoint path must start with /", 400);
          }

          try {
            const endpointId = db.createCustomEndpoint(
              body.endpoint_name,
              body.endpoint_path,
              body.api_key,
              body.primary_model,
              body.fallback_model || null
            );
            return jsonResponse({ id: endpointId }, 201);
          } catch (error) {
            return errorResponse(error instanceof Error ? error.message : "Failed to create endpoint", 500);
          }
        }

        if (pathname.startsWith("/api/custom-endpoints/") && req.method === "GET") {
          const endpointId = parseId(pathname);
          const endpoint = db.getCustomEndpoint(endpointId);
          if (!endpoint) return errorResponse("Endpoint not found", 404);
          return jsonResponse(endpoint);
        }

        if (pathname.startsWith("/api/custom-endpoints/") && req.method === "PATCH") {
          const endpointId = parseId(pathname);
          const body = await req.json();
          db.updateCustomEndpoint(endpointId, body);
          return new Response(null, { status: 204 });
        }

        if (pathname.startsWith("/api/custom-endpoints/") && req.method === "DELETE") {
          const endpointId = parseId(pathname);
          db.deleteCustomEndpoint(endpointId);
          return new Response(null, { status: 204 });
        }

        // Playground chat proxy — forwards to the LLM gateway with the user's API key
        if (pathname === "/api/playground/chat" && req.method === "POST") {
          const authHeader = req.headers.get("authorization") || "";
          const sessionHeader = req.headers.get("x-session-id") || "";
          const gatewayBase = process.env.GATEWAY_URL || `http://localhost:${process.env.GATEWAY_PORT || 8008}`;
          const upstream = await fetch(`${gatewayBase}/v1/chat/completions`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: authHeader,
              ...(sessionHeader ? { "X-Session-ID": sessionHeader } : {}),
            },
            body: req.body,
          });
          return new Response(upstream.body, {
            status: upstream.status,
            headers: {
              "Content-Type": upstream.headers.get("Content-Type") || "application/json",
              "Cache-Control": "no-cache",
            },
          });
        }

        return errorResponse("Not found", 404);
      } catch (error) {
        return errorResponse(error instanceof Error ? error.message : "Server error", 500);
      }
    }

    if (pathname === "/") {
      return new Response(Bun.file(resolve(publicDir, "index.html")));
    }

    return await serveFile(pathname);
  },
});

console.log(`Dashboard running on http://localhost:${server.port}`);
