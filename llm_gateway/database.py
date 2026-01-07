import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


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
        
        # Models table with pricing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                input_cost_per_1k REAL DEFAULT 0.0,
                output_cost_per_1k REAL DEFAULT 0.0,
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
    def add_model(self, model_name: str, input_cost: float, output_cost: float) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO models (model_name, input_cost_per_1k, output_cost_per_1k)
            VALUES (?, ?, ?)
        """, (model_name, input_cost, output_cost))
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
        cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY model_name")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0],
            "model_name": row[1],
            "input_cost_per_1k": row[2],
            "output_cost_per_1k": row[3],
            "is_active": row[4],
            "created_at": row[5]
        } for row in rows]
    
    # Usage Logging
    def log_usage(self, api_key_id: int, user_id: int, model_name: str, 
                  input_tokens: int, output_tokens: int, response_time: float,
                  cost: float, endpoint: str, status: str, error_message: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        total_tokens = input_tokens + output_tokens
        cursor.execute("""
            INSERT INTO usage_logs 
            (api_key_id, user_id, model_name, input_tokens, output_tokens, 
             total_tokens, response_time, cost, endpoint, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (api_key_id, user_id, model_name, input_tokens, output_tokens,
              total_tokens, response_time, cost, endpoint, status, error_message))
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
