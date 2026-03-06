import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
from crypto_utils import encrypt_api_key, decrypt_api_key, mask_api_key

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "llm_gateway.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # API Keys table
        cursor.execute("""
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
            )
        """)

        # LLM Providers table
        cursor.execute("""
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
            )
        """)

        # Models table with pricing (updated to include provider_name)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                input_cost_per_1k REAL DEFAULT 0.0,
                output_cost_per_1k REAL DEFAULT 0.0,
                provider_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Usage logs table
        cursor.execute("""
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
            )
        """)

        # Check if provider_name column exists in models table, add if missing
        cursor.execute("PRAGMA table_info(models)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'provider_name' not in columns:
            logger.info("Adding provider_name column to models table")
            cursor.execute("ALTER TABLE models ADD COLUMN provider_name TEXT")

        # Create indexes (after ensuring columns exist)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_providers_active ON llm_providers(is_active)")

        conn.commit()
        conn.close()
    
    # User Management
    def create_user(self, username: str) -> Optional[int]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "created_at": row[2]}
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "created_at": row[2]}
        return None
    
    def get_all_users(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": row[0], "username": row[1], "created_at": row[2]} for row in rows]
    
    # API Key Management
    def create_api_key(self, user_id: int, api_key: str, allowed_models: List[str], cost_limit: float = 0.0) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (user_id, api_key, allowed_models, cost_limit)
            VALUES (?, ?, ?, ?)
        """, (user_id, api_key, json.dumps(allowed_models), cost_limit))
        api_key_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return api_key_id
    
    def get_api_key_info(self, api_key: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ak.*, u.username 
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.api_key = ? AND ak.is_active = 1
        """, (api_key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "api_key": row[2],
                "allowed_models": json.loads(row[3]),
                "cost_limit": row[4],
                "current_cost": row[5],
                "is_active": row[6],
                "created_at": row[7],
                "username": row[8]
            }
        return None
    
    def get_user_api_keys(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "user_id": row[1],
            "api_key": row[2],
            "allowed_models": json.loads(row[3]),
            "cost_limit": row[4],
            "current_cost": row[5],
            "is_active": row[6],
            "created_at": row[7]
        } for row in rows]
    
    def update_api_key_cost(self, api_key_id: int, cost: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE api_keys 
            SET current_cost = current_cost + ?
            WHERE id = ?
        """, (cost, api_key_id))
        conn.commit()
        conn.close()
    
    def deactivate_api_key(self, api_key_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (api_key_id,))
        conn.commit()
        conn.close()

    def activate_api_key(self, api_key_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 1 WHERE id = ?", (api_key_id,))
        conn.commit()
        conn.close()

    def delete_api_key(self, api_key_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usage_logs WHERE api_key_id = ?", (api_key_id,))
        cursor.execute("DELETE FROM api_keys WHERE id = ?", (api_key_id,))
        conn.commit()
        conn.close()

    def delete_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Delete user's API keys first
        cursor.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
        # Delete user's usage logs
        cursor.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    def delete_model(self, model_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
        conn.close()

    def get_all_api_keys(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ak.*, u.username 
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            ORDER BY ak.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "user_id": row[1],
            "api_key": row[2],
            "allowed_models": json.loads(row[3]),
            "cost_limit": row[4],
            "current_cost": row[5],
            "is_active": row[6],
            "created_at": row[7],
            "username": row[8]
        } for row in rows]
    
    # Model Management
    def add_model(self, model_name: str, input_cost: float, output_cost: float, provider_name: Optional[str] = None) -> int:
        """Add or update model (backward compatible, provider_name is optional)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO models (model_name, input_cost_per_1k, output_cost_per_1k, provider_name)
            VALUES (?, ?, ?, ?)
        """, (model_name, input_cost, output_cost, provider_name))
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id
    
    def get_model_pricing(self, model_name: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE model_name = ? AND is_active = 1", (model_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "model_name": row[1],
                "input_cost_per_1k": row[2],
                "output_cost_per_1k": row[3],
                "is_active": row[4],
                "created_at": row[5]
            }
        return None
    
    def get_all_models(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, model_name, input_cost_per_1k, output_cost_per_1k, is_active, created_at, provider_name FROM models WHERE is_active = 1 ORDER BY model_name")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "model_name": row[1],
            "input_cost_per_1k": row[2],
            "output_cost_per_1k": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "provider_name": row[6]
        } for row in rows]
    
    # Usage Logging
    def log_usage(self, api_key_id: int, user_id: int, model_name: str,
                  input_tokens: int, output_tokens: int, response_time: float,
                  cost: float, endpoint: str, status: str, error_message: str = None,
                  trace_id: str = None, session_id: str = None,
                  request_payload: str = None, response_payload: str = None,
                  system_message: str = None, user_message: str = None,
                  assistant_message: str = None, assistant_tool_calls: str = None,
                  tool_responses: str = None, stream_setting: str = None,
                  temperature: float = None, tool_call_type: str = None,
                  tool_name: str = None, org_id: int = None, request_time: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        total_tokens = input_tokens + output_tokens
        cursor.execute("""
            INSERT INTO usage_logs
            (api_key_id, user_id, model_name, input_tokens, output_tokens,
             total_tokens, response_time, cost, endpoint, status, error_message,
             trace_id, session_id, request_payload, response_payload,
             system_message, user_message, assistant_message, assistant_tool_calls,
             tool_responses, stream_setting, temperature, tool_call_type,
             tool_name, org_id, request_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (api_key_id, user_id, model_name, input_tokens, output_tokens,
              total_tokens, response_time, cost, endpoint, status, error_message,
              trace_id, session_id, request_payload, response_payload,
              system_message, user_message, assistant_message, assistant_tool_calls,
              tool_responses, stream_setting, temperature, tool_call_type,
              tool_name, org_id, request_time))
        conn.commit()
        conn.close()
    
    # Analytics
    def get_usage_stats(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT * FROM usage_logs 
                WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """, (user_id, days))
        else:
            cursor.execute("""
                SELECT * FROM usage_logs 
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """, (days,))
        
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "api_key_id": row[1],
            "user_id": row[2],
            "model_name": row[3],
            "input_tokens": row[4],
            "output_tokens": row[5],
            "total_tokens": row[6],
            "response_time": row[7],
            "cost": row[8],
            "endpoint": row[9],
            "status": row[10],
            "error_message": row[11],
            "created_at": row[12]
        } for row in rows]
    
    def get_summary_stats(self, user_id: Optional[int] = None) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost) as total_cost,
                    AVG(response_time) as avg_response_time
                FROM usage_logs
                WHERE user_id = ?
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost) as total_cost,
                    AVG(response_time) as avg_response_time
                FROM usage_logs
            """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total_requests": row[0] or 0,
            "total_input_tokens": row[1] or 0,
            "total_output_tokens": row[2] or 0,
            "total_tokens": row[3] or 0,
            "total_cost": row[4] or 0.0,
            "avg_response_time": row[5] or 0.0
        }

    # LLM Provider Management
    def create_provider(self, provider_name: str, base_url: str, api_key: Optional[str] = None,
                       allowed_models: Optional[List[str]] = None) -> int:
        """Create a new LLM provider with encrypted API key"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Encrypt API key if provided
        encrypted_key = encrypt_api_key(api_key) if api_key else None
        allowed_models_json = json.dumps(allowed_models if allowed_models else [])

        try:
            cursor.execute("""
                INSERT INTO llm_providers (provider_name, base_url, api_key, allowed_models, health_status)
                VALUES (?, ?, ?, ?, 'unknown')
            """, (provider_name, base_url, encrypted_key, allowed_models_json))
            provider_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created provider: {provider_name} with ID: {provider_id}")
            return provider_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Provider {provider_name} already exists")
            raise
        finally:
            conn.close()

    def get_provider(self, provider_id: int) -> Optional[Dict]:
        """Get provider by ID with decrypted API key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM llm_providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "provider_name": row[1],
                "base_url": row[2],
                "api_key": decrypt_api_key(row[3]) if row[3] else None,
                "api_key_masked": mask_api_key(decrypt_api_key(row[3])) if row[3] else None,
                "allowed_models": json.loads(row[4]) if row[4] else [],
                "is_active": row[5],
                "last_health_check": row[6],
                "health_status": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
        return None

    def get_provider_by_name(self, provider_name: str) -> Optional[Dict]:
        """Get provider by name with decrypted API key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM llm_providers WHERE provider_name = ?", (provider_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "provider_name": row[1],
                "base_url": row[2],
                "api_key": decrypt_api_key(row[3]) if row[3] else None,
                "api_key_masked": mask_api_key(decrypt_api_key(row[3])) if row[3] else None,
                "allowed_models": json.loads(row[4]) if row[4] else [],
                "is_active": row[5],
                "last_health_check": row[6],
                "health_status": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
        return None

    def get_all_providers(self, include_inactive: bool = True) -> List[Dict]:
        """Get all providers with masked API keys (for UI display)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if include_inactive:
            cursor.execute("SELECT * FROM llm_providers ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM llm_providers WHERE is_active = 1 ORDER BY created_at DESC")

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "provider_name": row[1],
            "base_url": row[2],
            "api_key_masked": mask_api_key(decrypt_api_key(row[3])) if row[3] else None,
            "allowed_models": json.loads(row[4]) if row[4] else [],
            "is_active": row[5],
            "last_health_check": row[6],
            "health_status": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        } for row in rows]

    def update_provider(self, provider_id: int, provider_name: Optional[str] = None,
                       base_url: Optional[str] = None, api_key: Optional[str] = None,
                       allowed_models: Optional[List[str]] = None, is_active: Optional[bool] = None) -> bool:
        """Update provider details"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if provider_name is not None:
            updates.append("provider_name = ?")
            params.append(provider_name)

        if base_url is not None:
            updates.append("base_url = ?")
            params.append(base_url)

        if api_key is not None:
            updates.append("api_key = ?")
            params.append(encrypt_api_key(api_key))

        if allowed_models is not None:
            updates.append("allowed_models = ?")
            params.append(json.dumps(allowed_models))

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            conn.close()
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(provider_id)

        cursor.execute(f"""
            UPDATE llm_providers
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)

        affected = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Updated provider ID {provider_id}, affected rows: {affected}")
        return affected > 0

    def update_provider_health(self, provider_id: int, health_status: str):
        """Update provider health check status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE llm_providers
            SET health_status = ?, last_health_check = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (health_status, provider_id))
        conn.commit()
        conn.close()

    def delete_provider(self, provider_id: int):
        """Delete provider and set associated models to inactive"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get provider name first
        cursor.execute("SELECT provider_name FROM llm_providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        provider_name = row[0]

        # Set models associated with this provider to inactive
        cursor.execute("UPDATE models SET is_active = 0 WHERE provider_name = ?", (provider_name,))

        # Delete the provider
        cursor.execute("DELETE FROM llm_providers WHERE id = ?", (provider_id,))

        conn.commit()
        conn.close()
        logger.info(f"Deleted provider ID {provider_id} ({provider_name})")

    def get_provider_by_model(self, model_name: str) -> Optional[Dict]:
        """Get provider information by model name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # First, get the model to find its provider
        cursor.execute("SELECT provider_name FROM models WHERE model_name = ? AND is_active = 1", (model_name,))
        row = cursor.fetchone()

        if not row or not row[0]:
            conn.close()
            return None

        provider_name = row[0]

        # Then get the provider details
        cursor.execute("SELECT * FROM llm_providers WHERE provider_name = ? AND is_active = 1", (provider_name,))
        provider_row = cursor.fetchone()
        conn.close()

        if provider_row:
            return {
                "id": provider_row[0],
                "provider_name": provider_row[1],
                "base_url": provider_row[2],
                "api_key": decrypt_api_key(provider_row[3]) if provider_row[3] else None,
                "allowed_models": json.loads(provider_row[4]) if provider_row[4] else [],
                "is_active": provider_row[5],
                "last_health_check": provider_row[6],
                "health_status": provider_row[7],
                "created_at": provider_row[8],
                "updated_at": provider_row[9]
            }
        return None

    # Update existing model methods to support provider association
    def add_model_with_provider(self, model_name: str, input_cost: float, output_cost: float,
                                provider_name: Optional[str] = None) -> int:
        """Add or update model with provider association"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO models (model_name, input_cost_per_1k, output_cost_per_1k, provider_name)
            VALUES (?, ?, ?, ?)
        """, (model_name, input_cost, output_cost, provider_name))
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added/updated model: {model_name} for provider: {provider_name}")
        return model_id

    def get_models_by_provider(self, provider_name: str) -> List[Dict]:
        """Get all models for a specific provider"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM models
            WHERE provider_name = ? AND is_active = 1
            ORDER BY model_name
        """, (provider_name,))
        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "model_name": row[1],
            "input_cost_per_1k": row[2],
            "output_cost_per_1k": row[3],
            "provider_name": row[4],
            "is_active": row[5],
            "created_at": row[6]
        } for row in rows]
