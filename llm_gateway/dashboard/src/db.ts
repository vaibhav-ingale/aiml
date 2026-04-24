import { Database as SQLiteDatabase } from "bun:sqlite";

function maskApiKey(apiKey: string | null, visibleChars: number = 4): string {
  if (!apiKey || apiKey.length <= visibleChars) {
    return "****";
  }
  return "*".repeat(8) + apiKey.slice(-visibleChars);
}

export class Database {
  private db: SQLiteDatabase;

  constructor(dbPath: string) {
    this.db = new SQLiteDatabase(dbPath);
    this.db.exec("PRAGMA foreign_keys = ON;");
    this.initDb();
  }

  private initDb() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        allowed_models TEXT NOT NULL,
        cost_limit REAL DEFAULT 0.0,
        current_cost REAL DEFAULT 0.0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
      );

      CREATE TABLE IF NOT EXISTS llm_providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name TEXT UNIQUE NOT NULL,
        base_url TEXT NOT NULL,
        api_key TEXT,
        allowed_models TEXT,
        is_active BOOLEAN DEFAULT 1,
        last_health_check TIMESTAMP,
        health_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT UNIQUE NOT NULL,
        input_cost_per_1k REAL DEFAULT 0.0,
        output_cost_per_1k REAL DEFAULT 0.0,
        provider_name TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trace_id TEXT,
        session_id TEXT,
        api_key_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        input_tokens INTEGER,
        output_tokens INTEGER,
        total_tokens INTEGER,
        response_time REAL,
        cost REAL,
        endpoint TEXT,
        status TEXT,
        error_message TEXT,
        request_payload TEXT,
        response_payload TEXT,
        system_message TEXT,
        user_message TEXT,
        assistant_message TEXT,
        assistant_tool_calls TEXT,
        tool_responses TEXT,
        stream_setting INTEGER,
        temperature REAL,
        tool_call_type TEXT,
        tool_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
      );

      CREATE TABLE IF NOT EXISTS custom_endpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint_name TEXT UNIQUE NOT NULL,
        endpoint_path TEXT UNIQUE NOT NULL,
        api_key TEXT NOT NULL,
        primary_model TEXT NOT NULL,
        fallback_model TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_created_at ON usage_logs(created_at DESC);
      CREATE INDEX IF NOT EXISTS idx_providers_active ON llm_providers(is_active);
      CREATE INDEX IF NOT EXISTS idx_custom_endpoints_path ON custom_endpoints(endpoint_path);
      CREATE INDEX IF NOT EXISTS idx_custom_endpoints_active ON custom_endpoints(is_active);
    `);

    // Migrate models table
    const modelsInfo = this.db.query("PRAGMA table_info(models)").all() as any[];
    const modelsColumns = new Set(modelsInfo.map((col: any) => col.name));
    if (!modelsColumns.has("provider_name")) {
      this.db.exec("ALTER TABLE models ADD COLUMN provider_name TEXT");
    }

    // Migrate usage_logs table
    const logsInfo = this.db.query("PRAGMA table_info(usage_logs)").all() as any[];
    const logsColumns = new Set(logsInfo.map((col: any) => col.name));
    const missingLogsCols: [string, string][] = [
      ["trace_id", "TEXT"],
      ["session_id", "TEXT"],
      ["request_payload", "TEXT"],
      ["response_payload", "TEXT"],
      ["system_message", "TEXT"],
      ["user_message", "TEXT"],
      ["assistant_message", "TEXT"],
      ["assistant_tool_calls", "TEXT"],
      ["tool_responses", "TEXT"],
      ["stream_setting", "INTEGER"],
      ["temperature", "REAL"],
      ["tool_call_type", "TEXT"],
      ["tool_name", "TEXT"],
    ];
    for (const [col, type] of missingLogsCols) {
      if (!logsColumns.has(col)) {
        this.db.exec(`ALTER TABLE usage_logs ADD COLUMN ${col} ${type}`);
      }
    }

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_trace_id ON usage_logs(trace_id);
      CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_name);
    `);
  }

  createUser(username: string) {
    try {
      const info = this.db.query("INSERT INTO users (username) VALUES (?)").run(username);
      return Number(info.lastInsertRowid);
    } catch {
      return null;
    }
  }

  getUser(userId: number) {
    return this.db.query("SELECT * FROM users WHERE id = ?").get(userId) as any;
  }

  getUserByUsername(username: string) {
    return this.db.query("SELECT * FROM users WHERE username = ?").get(username) as any;
  }

  getAllUsers() {
    return this.db.query("SELECT * FROM users ORDER BY created_at DESC").all() as any[];
  }

  deleteUser(userId: number) {
    const stmt = this.db.transaction(() => {
      this.db.query("DELETE FROM api_keys WHERE user_id = ?").run(userId);
      this.db.query("DELETE FROM usage_logs WHERE user_id = ?").run(userId);
      this.db.query("DELETE FROM users WHERE id = ?").run(userId);
    });
    stmt();
  }

  createApiKey(userId: number, apiKey: string, allowedModels: string[], costLimit: number) {
    const info = this.db
      .query(
        "INSERT INTO api_keys (user_id, api_key, allowed_models, cost_limit) VALUES (?, ?, ?, ?)"
      )
      .run(userId, apiKey, JSON.stringify(allowedModels), costLimit);
    return Number(info.lastInsertRowid);
  }

  getAllApiKeys() {
    const rows = this.db
      .query(
        `SELECT ak.*, u.username
         FROM api_keys ak
         JOIN users u ON ak.user_id = u.id
         ORDER BY ak.created_at DESC`
      )
      .all() as any[];

    return rows.map((row) => ({
      ...row,
      allowed_models: JSON.parse(row.allowed_models),
    }));
  }

  getApiKeyById(apiKeyId: number) {
    const row = this.db.query("SELECT * FROM api_keys WHERE id = ?").get(apiKeyId) as any;
    if (!row) return null;
    return {
      ...row,
      allowed_models: JSON.parse(row.allowed_models),
    };
  }

  getUserApiKeys(userId: number) {
    const rows = this.db
      .query("SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC")
      .all(userId) as any[];
    return rows.map((row) => ({
      ...row,
      allowed_models: JSON.parse(row.allowed_models),
    }));
  }

  updateApiKeyStatus(apiKeyId: number, isActive: boolean) {
    this.db.query("UPDATE api_keys SET is_active = ? WHERE id = ?").run(isActive ? 1 : 0, apiKeyId);
  }

  deleteApiKey(apiKeyId: number) {
    const stmt = this.db.transaction(() => {
      this.db.query("DELETE FROM usage_logs WHERE api_key_id = ?").run(apiKeyId);
      this.db.query("DELETE FROM api_keys WHERE id = ?").run(apiKeyId);
    });
    stmt();
  }

  addModel(modelName: string, inputCost: number, outputCost: number, providerName: string | null = null) {
    // Check if model exists
    const existing = this.db.query("SELECT id FROM models WHERE model_name = ?").get(modelName) as any;

    if (existing) {
      // Update existing model - only update pricing, leave provider_name untouched
      this.db.query(
        "UPDATE models SET input_cost_per_1k = ?, output_cost_per_1k = ? WHERE model_name = ?"
      ).run(inputCost, outputCost, modelName);
      return existing.id;
    } else {
      // Insert new model
      const info = this.db.query(
        "INSERT INTO models (model_name, input_cost_per_1k, output_cost_per_1k, provider_name) VALUES (?, ?, ?, ?)"
      ).run(modelName, inputCost, outputCost, providerName);
      return Number(info.lastInsertRowid);
    }
  }

  // Add model only if it doesn't exist (for provider refresh)
  addModelIfNotExists(modelName: string, inputCost: number, outputCost: number, providerName: string | null = null): number | null {
    // Check if model exists
    const existing = this.db.query("SELECT id FROM models WHERE model_name = ?").get(modelName) as any;

    if (existing) {
      // Model exists - do nothing, return null to indicate it wasn't added
      return null;
    } else {
      // Insert new model only
      const info = this.db.query(
        "INSERT INTO models (model_name, input_cost_per_1k, output_cost_per_1k, provider_name) VALUES (?, ?, ?, ?)"
      ).run(modelName, inputCost, outputCost, providerName);
      return Number(info.lastInsertRowid);
    }
  }

  getAllModels() {
    return this.db
      .query("SELECT * FROM models WHERE is_active = 1 ORDER BY model_name")
      .all() as any[];
  }

  deleteModel(modelId: number) {
    this.db.query("DELETE FROM models WHERE id = ?").run(modelId);
  }

  getUsageStats(userId: number | null, days: number) {
    if (userId) {
      return this.db
        .query(
          `SELECT * FROM usage_logs
           WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
           ORDER BY created_at DESC`
        )
        .all(userId, days) as any[];
    }

    return this.db
      .query(
        `SELECT * FROM usage_logs
         WHERE created_at >= datetime('now', '-' || ? || ' days')
         ORDER BY created_at DESC`
      )
      .all(days) as any[];
  }

  getSummaryStats(userId: number | null) {
    let row;
    if (userId) {
      row = this.db
        .query(
          `SELECT
            COUNT(*) as total_requests,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost,
            AVG(response_time) as avg_response_time
          FROM usage_logs
          WHERE user_id = ?`
        )
        .get(userId) as any;
    } else {
      row = this.db
        .query(
          `SELECT
            COUNT(*) as total_requests,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost,
            AVG(response_time) as avg_response_time
          FROM usage_logs`
        )
        .get() as any;
    }

    return {
      total_requests: row?.total_requests || 0,
      total_input_tokens: row?.total_input_tokens || 0,
      total_output_tokens: row?.total_output_tokens || 0,
      total_tokens: row?.total_tokens || 0,
      total_cost: row?.total_cost || 0,
      avg_response_time: row?.avg_response_time || 0,
    };
  }

  getTraces(limit = 100, offset = 0, userId: number | null = null, sessionId: string | null = null) {
    let query = `
      SELECT
        ul.id,
        ul.trace_id,
        ul.session_id,
        ul.created_at as timestamp,
        ul.model_name,
        ul.input_tokens,
        ul.output_tokens,
        ul.total_tokens,
        ul.response_time,
        ul.cost,
        ul.status,
        ul.user_id,
        ul.user_message,
        ul.assistant_message,
        ul.tool_name,
        ul.tool_call_type,
        m.provider_name
      FROM usage_logs ul
      LEFT JOIN models m ON ul.model_name = m.model_name
    `;

    const params: any[] = [];
    const conditions: string[] = [];

    if (userId !== null) {
      conditions.push('ul.user_id = ?');
      params.push(userId);
    }

    if (sessionId !== null && sessionId !== '') {
      conditions.push('ul.session_id = ?');
      params.push(sessionId);
    }

    if (conditions.length > 0) {
      query += ` WHERE ${conditions.join(' AND ')}`;
    }

    query += ` ORDER BY ul.created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);

    return this.db.query(query).all(...params) as any[];
  }

  getTraceById(traceId: string | number) {
    // Convert to number if it's a numeric string
    const numericId = Number(traceId);
    const isNumeric = !isNaN(numericId);

    let row;
    if (isNumeric) {
      // If it's a valid number, search by both trace_id string and id number
      row = this.db
        .query(
          `SELECT
            ul.id,
            ul.trace_id,
            ul.session_id,
            ul.created_at as timestamp,
            ul.model_name,
            ul.input_tokens,
            ul.output_tokens,
            ul.total_tokens,
            ul.response_time,
            ul.cost,
            ul.status,
            ul.error_message,
            ul.request_payload,
            ul.response_payload,
            ul.system_message,
            ul.user_message,
            ul.assistant_message,
            ul.assistant_tool_calls,
            ul.tool_responses,
            ul.stream_setting,
            ul.temperature,
            ul.tool_call_type,
            ul.tool_name,
            ul.endpoint,
            ul.user_id,
            ul.api_key_id,
            m.provider_name
          FROM usage_logs ul
          LEFT JOIN models m ON ul.model_name = m.model_name
          WHERE ul.trace_id = ? OR ul.id = ?`
        )
        .get(String(traceId), numericId) as any;
    } else {
      // If it's a non-numeric string, only search by trace_id
      row = this.db
        .query(
          `SELECT
            ul.id,
            ul.trace_id,
            ul.session_id,
            ul.created_at as timestamp,
            ul.model_name,
            ul.input_tokens,
            ul.output_tokens,
            ul.total_tokens,
            ul.response_time,
            ul.cost,
            ul.status,
            ul.error_message,
            ul.request_payload,
            ul.response_payload,
            ul.system_message,
            ul.user_message,
            ul.assistant_message,
            ul.assistant_tool_calls,
            ul.tool_responses,
            ul.stream_setting,
            ul.temperature,
            ul.tool_call_type,
            ul.tool_name,
            ul.endpoint,
            ul.user_id,
            ul.api_key_id,
            m.provider_name
          FROM usage_logs ul
          LEFT JOIN models m ON ul.model_name = m.model_name
          WHERE ul.trace_id = ?`
        )
        .get(String(traceId)) as any;
    }

    if (!row) return null;

    // Parse JSON fields if they exist
    if (row.request_payload) {
      try {
        row.request_payload = JSON.parse(row.request_payload);
      } catch {
        // Keep as string if parsing fails
      }
    }

    if (row.response_payload) {
      try {
        row.response_payload = JSON.parse(row.response_payload);
      } catch {
        // Keep as string if parsing fails
      }
    }

    if (row.assistant_tool_calls) {
      try {
        row.assistant_tool_calls = JSON.parse(row.assistant_tool_calls);
      } catch {
        // Keep as string if parsing fails
      }
    }

    if (row.tool_responses) {
      try {
        row.tool_responses = JSON.parse(row.tool_responses);
      } catch {
        // Keep as string if parsing fails
      }
    }

    return row;
  }

  getTraceCount(userId: number | null = null, sessionId: string | null = null) {
    let query = `SELECT COUNT(*) as count FROM usage_logs`;
    const params: any[] = [];
    const conditions: string[] = [];

    if (userId !== null) {
      conditions.push('user_id = ?');
      params.push(userId);
    }

    if (sessionId !== null && sessionId !== '') {
      conditions.push('session_id = ?');
      params.push(sessionId);
    }

    if (conditions.length > 0) {
      query += ` WHERE ${conditions.join(' AND ')}`;
    }

    const row = this.db.query(query).get(...params) as any;
    return row?.count || 0;
  }

  clearAllTraces() {
    this.db.query("DELETE FROM usage_logs").run();
    return true;
  }

  deleteTraces(traceIds: string[]) {
    if (!traceIds || traceIds.length === 0) return 0;

    // Build query with placeholders for trace_id OR id matching
    const conditions = traceIds.map(() => "(trace_id = ? OR id = ?)").join(" OR ");
    const query = `DELETE FROM usage_logs WHERE ${conditions}`;

    // Flatten the array: each traceId appears twice for the OR condition
    const params = traceIds.flatMap((id) => [id, id]);

    const result = this.db.query(query).run(...params);
    return result.changes;
  }

  getUniqueSessions() {
    const rows = this.db.query(`
      SELECT DISTINCT session_id, COUNT(*) as trace_count, MAX(created_at) as last_activity
      FROM usage_logs
      WHERE session_id IS NOT NULL AND session_id != ''
      GROUP BY session_id
      ORDER BY last_activity DESC
    `).all() as any[];

    return rows.map((row) => ({
      session_id: row.session_id,
      trace_count: row.trace_count,
      last_activity: row.last_activity,
    }));
  }

  // LLM Provider Management
  createProvider(providerName: string, baseUrl: string, apiKey: string | null, allowedModels: string[]) {
    const info = this.db
      .query(
        `INSERT INTO llm_providers (provider_name, base_url, api_key, allowed_models, health_status)
         VALUES (?, ?, ?, ?, 'unknown')`
      )
      .run(providerName, baseUrl, apiKey, JSON.stringify(allowedModels));
    return Number(info.lastInsertRowid);
  }

  getProvider(providerId: number) {
    const row = this.db.query("SELECT * FROM llm_providers WHERE id = ?").get(providerId) as any;
    if (!row) return null;

    return {
      ...row,
      api_key_masked: maskApiKey(row.api_key),
      allowed_models: row.allowed_models ? JSON.parse(row.allowed_models) : [],
    };
  }

  getProviderByName(providerName: string) {
    const row = this.db.query("SELECT * FROM llm_providers WHERE provider_name = ?").get(providerName) as any;
    if (!row) return null;

    return {
      ...row,
      api_key_masked: maskApiKey(row.api_key),
      allowed_models: row.allowed_models ? JSON.parse(row.allowed_models) : [],
    };
  }

  getAllProviders(includeInactive: boolean = true) {
    let query = "SELECT * FROM llm_providers";
    if (!includeInactive) {
      query += " WHERE is_active = 1";
    }
    query += " ORDER BY created_at DESC";

    const rows = this.db.query(query).all() as any[];

    return rows.map((row) => ({
      ...row,
      api_key_masked: maskApiKey(row.api_key),
      allowed_models: row.allowed_models ? JSON.parse(row.allowed_models) : [],
    }));
  }

  updateProvider(
    providerId: number,
    updates: {
      provider_name?: string;
      base_url?: string;
      api_key?: string;
      allowed_models?: string[];
      is_active?: boolean;
    }
  ) {
    const fields: string[] = [];
    const values: any[] = [];

    if (updates.provider_name !== undefined) {
      fields.push("provider_name = ?");
      values.push(updates.provider_name);
    }
    if (updates.base_url !== undefined) {
      fields.push("base_url = ?");
      values.push(updates.base_url);
    }
    if (updates.api_key !== undefined) {
      fields.push("api_key = ?");
      values.push(updates.api_key);
    }
    if (updates.allowed_models !== undefined) {
      fields.push("allowed_models = ?");
      values.push(JSON.stringify(updates.allowed_models));
    }
    if (updates.is_active !== undefined) {
      fields.push("is_active = ?");
      values.push(updates.is_active ? 1 : 0);
    }

    if (fields.length === 0) return;

    fields.push("updated_at = CURRENT_TIMESTAMP");
    values.push(providerId);

    const query = `UPDATE llm_providers SET ${fields.join(", ")} WHERE id = ?`;
    this.db.query(query).run(...values);
  }

  updateProviderHealth(providerId: number, healthStatus: string) {
    this.db
      .query(
        `UPDATE llm_providers
         SET health_status = ?, last_health_check = CURRENT_TIMESTAMP
         WHERE id = ?`
      )
      .run(healthStatus, providerId);
  }

  deleteProvider(providerId: number) {
    // Get provider name
    const provider = this.db.query("SELECT provider_name FROM llm_providers WHERE id = ?").get(providerId) as any;
    if (!provider) return;

    const stmt = this.db.transaction(() => {
      // Set models associated with this provider to inactive
      this.db.query("UPDATE models SET is_active = 0 WHERE provider_name = ?").run(provider.provider_name);
      // Delete the provider
      this.db.query("DELETE FROM llm_providers WHERE id = ?").run(providerId);
    });
    stmt();
  }

  getProviderByModel(modelName: string) {
    const model = this.db
      .query("SELECT provider_name FROM models WHERE model_name = ? AND is_active = 1")
      .get(modelName) as any;

    if (!model || !model.provider_name) return null;

    return this.getProviderByName(model.provider_name);
  }


  getModelsByProvider(providerName: string) {
    return this.db
      .query("SELECT * FROM models WHERE provider_name = ? AND is_active = 1 ORDER BY model_name")
      .all(providerName) as any[];
  }

  // Custom Endpoint Management
  createCustomEndpoint(
    endpointName: string,
    endpointPath: string,
    apiKey: string,
    primaryModel: string,
    fallbackModel: string | null
  ) {
    const info = this.db
      .query(
        `INSERT INTO custom_endpoints (endpoint_name, endpoint_path, api_key, primary_model, fallback_model)
         VALUES (?, ?, ?, ?, ?)`
      )
      .run(endpointName, endpointPath, apiKey, primaryModel, fallbackModel);
    return Number(info.lastInsertRowid);
  }

  getCustomEndpoint(endpointId: number) {
    const row = this.db.query("SELECT * FROM custom_endpoints WHERE id = ?").get(endpointId) as any;
    if (!row) return null;

    return {
      ...row,
      api_key_masked: maskApiKey(row.api_key),
    };
  }

  getCustomEndpointByPath(endpointPath: string) {
    const row = this.db
      .query("SELECT * FROM custom_endpoints WHERE endpoint_path = ? AND is_active = 1")
      .get(endpointPath) as any;
    if (!row) return null;

    return {
      ...row,
      api_key_masked: maskApiKey(row.api_key),
    };
  }

  getAllCustomEndpoints(includeInactive: boolean = true) {
    let query = "SELECT * FROM custom_endpoints";
    if (!includeInactive) {
      query += " WHERE is_active = 1";
    }
    query += " ORDER BY created_at DESC";

    const rows = this.db.query(query).all() as any[];

    return rows.map((row) => ({
      ...row,
      api_key_masked: maskApiKey(row.api_key),
    }));
  }

  updateCustomEndpoint(
    endpointId: number,
    updates: {
      endpoint_name?: string;
      endpoint_path?: string;
      api_key?: string;
      primary_model?: string;
      fallback_model?: string | null;
      is_active?: boolean;
    }
  ) {
    const fields: string[] = [];
    const values: any[] = [];

    if (updates.endpoint_name !== undefined) {
      fields.push("endpoint_name = ?");
      values.push(updates.endpoint_name);
    }
    if (updates.endpoint_path !== undefined) {
      fields.push("endpoint_path = ?");
      values.push(updates.endpoint_path);
    }
    if (updates.api_key !== undefined) {
      fields.push("api_key = ?");
      values.push(updates.api_key);
    }
    if (updates.primary_model !== undefined) {
      fields.push("primary_model = ?");
      values.push(updates.primary_model);
    }
    if (updates.fallback_model !== undefined) {
      fields.push("fallback_model = ?");
      values.push(updates.fallback_model);
    }
    if (updates.is_active !== undefined) {
      fields.push("is_active = ?");
      values.push(updates.is_active ? 1 : 0);
    }

    if (fields.length === 0) return;

    fields.push("updated_at = CURRENT_TIMESTAMP");
    values.push(endpointId);

    const query = `UPDATE custom_endpoints SET ${fields.join(", ")} WHERE id = ?`;
    this.db.query(query).run(...values);
  }

  deleteCustomEndpoint(endpointId: number) {
    this.db.query("DELETE FROM custom_endpoints WHERE id = ?").run(endpointId);
  }
}
