import { Database as SQLiteDatabase } from "bun:sqlite";

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

      CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT UNIQUE NOT NULL,
        input_cost_per_1k REAL DEFAULT 0.0,
        output_cost_per_1k REAL DEFAULT 0.0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
      );

      CREATE INDEX IF NOT EXISTS idx_trace_id ON usage_logs(trace_id);
      CREATE INDEX IF NOT EXISTS idx_created_at ON usage_logs(created_at DESC);
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

  addModel(modelName: string, inputCost: number, outputCost: number) {
    const info = this.db
      .query(
        "INSERT OR REPLACE INTO models (model_name, input_cost_per_1k, output_cost_per_1k) VALUES (?, ?, ?)"
      )
      .run(modelName, inputCost, outputCost);
    return Number(info.lastInsertRowid);
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
        id,
        trace_id,
        session_id,
        created_at as timestamp,
        model_name,
        input_tokens,
        output_tokens,
        total_tokens,
        response_time,
        cost,
        status,
        user_id,
        user_message,
        assistant_message,
        tool_name,
        tool_call_type
      FROM usage_logs
    `;

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

    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
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
            id,
            trace_id,
            session_id,
            created_at as timestamp,
            model_name,
            input_tokens,
            output_tokens,
            total_tokens,
            response_time,
            cost,
            status,
            error_message,
            request_payload,
            response_payload,
            system_message,
            user_message,
            assistant_message,
            assistant_tool_calls,
            tool_responses,
            stream_setting,
            temperature,
            tool_call_type,
            tool_name,
            endpoint,
            user_id,
            api_key_id
          FROM usage_logs
          WHERE trace_id = ? OR id = ?`
        )
        .get(String(traceId), numericId) as any;
    } else {
      // If it's a non-numeric string, only search by trace_id
      row = this.db
        .query(
          `SELECT
            id,
            trace_id,
            session_id,
            created_at as timestamp,
            model_name,
            input_tokens,
            output_tokens,
            total_tokens,
            response_time,
            cost,
            status,
            error_message,
            request_payload,
            response_payload,
            system_message,
            user_message,
            assistant_message,
            assistant_tool_calls,
            tool_responses,
            stream_setting,
            temperature,
            tool_call_type,
            tool_name,
            endpoint,
            user_id,
            api_key_id
          FROM usage_logs
          WHERE trace_id = ?`
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
}
