import sqlite3
import json
from app.models.db import get_connection

class ScoutSourceRepository:
    @staticmethod
    def create(name: str, url_pattern: str, request_method: str = "GET", 
              headers: str = "", enabled: bool = True) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO scout_source(name, url_pattern, request_method, headers, enabled) VALUES(?, ?, ?, ?, ?)",
                    (name, url_pattern, request_method, headers, 1 if enabled else 0)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scout_source ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM scout_source").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_source WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_name(name: str):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_source WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, name: str = None, url_pattern: str = None, request_method: str = None, 
              headers: str = None, enabled: bool = None) -> bool:
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if url_pattern:
            update_fields.append("url_pattern = ?")
            params.append(url_pattern)
        if request_method:
            update_fields.append("request_method = ?")
            params.append(request_method)
        if headers:
            update_fields.append("headers = ?")
            params.append(headers)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        update_fields.append("update_at = datetime('now')")

        if len(update_fields) == 1:
            return False

        params.append(id)
        update_sql = f"UPDATE scout_source SET {','.join(update_fields)} WHERE id = ?"

        try:
            with get_connection() as conn:
                conn.execute(update_sql, params)
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_source WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM scout_source WHERE id IN ({placeholders})", tuple(ids))
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def toggle_status(id: int) -> bool:
        with get_connection() as conn:
            conn.execute("UPDATE scout_source SET enabled = 1 - enabled WHERE id = ?", (id,))
            conn.commit()
        return True

    @staticmethod
    def get_enabled_sources():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM scout_source WHERE enabled = 1").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def parse_headers(headers_str: str) -> dict:
        """解析请求头字符串为字典"""
        headers = {}
        if not headers_str:
            return headers
        
        lines = headers_str.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers

    @staticmethod
    def format_headers(headers_dict: dict) -> str:
        """将字典格式化为请求头字符串"""
        return '\n'.join([f"{k}: {v}" for k, v in headers_dict.items()])
