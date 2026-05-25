import sqlite3
from app.models.db import get_connection

class ModelServiceRepository:
    @staticmethod
    def create(name: str, model: str, api_key: str, base_url: str, 
               max_tokens: int = 4096, temperature: float = 0.7, is_default: bool = False) -> bool:
        try:
            with get_connection() as conn:
                if is_default:
                    conn.execute("UPDATE model_service SET is_default = 0")
                
                conn.execute(
                    """
                    INSERT INTO model_service(name, model, api_key, base_url, max_tokens, temperature, is_default)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, model, api_key, base_url, max_tokens, temperature, 1 if is_default else 0)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_all(page: int = 1, page_size: int = 6):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM model_service ORDER BY is_default DESC, create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM model_service").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM model_service WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_name(name: str):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM model_service WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_default():
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM model_service WHERE is_default = 1").fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all_options():
        with get_connection() as conn:
            rows = conn.execute("SELECT id, name FROM model_service ORDER BY is_default DESC, create_at DESC").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update(id: int, name: str = None, model: str = None, api_key: str = None, 
               base_url: str = None, max_tokens: int = None, temperature: float = None, 
               is_default: bool = None) -> bool:
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if model:
            update_fields.append("model = ?")
            params.append(model)
        if api_key:
            update_fields.append("api_key = ?")
            params.append(api_key)
        if base_url:
            update_fields.append("base_url = ?")
            params.append(base_url)
        if max_tokens:
            update_fields.append("max_tokens = ?")
            params.append(max_tokens)
        if temperature:
            update_fields.append("temperature = ?")
            params.append(temperature)
        if is_default is not None:
            update_fields.append("is_default = ?")
            params.append(1 if is_default else 0)
        
        update_fields.append("update_at = datetime('now')")

        if len(update_fields) == 1:
            return False

        params.append(id)
        update_sql = f"UPDATE model_service SET {','.join(update_fields)} WHERE id = ?"

        try:
            with get_connection() as conn:
                if is_default:
                    conn.execute("UPDATE model_service SET is_default = 0 WHERE id != ?", (id,))
                
                conn.execute(update_sql, params)
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM model_service WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def update_token_usage(id: int, tokens: int):
        with get_connection() as conn:
            conn.execute(
                "UPDATE model_service SET token_usage = token_usage + ? WHERE id = ?",
                (tokens, id)
            )
            conn.commit()

    @staticmethod
    def get_token_stats():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT name, token_usage FROM model_service ORDER BY token_usage DESC"
            ).fetchall()
        return [dict(row) for row in rows]
