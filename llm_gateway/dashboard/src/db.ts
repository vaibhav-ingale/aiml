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
}
