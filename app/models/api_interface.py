import sqlite3
from app.models.db import get_connection

class ApiInterfaceRepository:
    @staticmethod
    def create(name: str, url: str, method: str = "GET", response_format: str = "JSON",
               example: str = "", qps_limit: str = "", token_required: bool = False,
               remark: str = "", enabled: bool = True) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO api_interface(name, url, method, response_format, example, qps_limit, token_required, remark, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, url, method, response_format, example, qps_limit, 1 if token_required else 0, remark, 1 if enabled else 0)
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
                "SELECT * FROM api_interface ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM api_interface").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM api_interface WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, name: str = None, url: str = None, method: str = None,
               response_format: str = None, example: str = None, qps_limit: str = None,
               token_required: bool = None, remark: str = None, enabled: bool = None) -> bool:
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if url:
            update_fields.append("url = ?")
            params.append(url)
        if method:
            update_fields.append("method = ?")
            params.append(method)
        if response_format:
            update_fields.append("response_format = ?")
            params.append(response_format)
        if example is not None:
            update_fields.append("example = ?")
            params.append(example)
        if qps_limit is not None:
            update_fields.append("qps_limit = ?")
            params.append(qps_limit)
        if token_required is not None:
            update_fields.append("token_required = ?")
            params.append(1 if token_required else 0)
        if remark is not None:
            update_fields.append("remark = ?")
            params.append(remark)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        update_fields.append("update_at = datetime('now')")

        if len(update_fields) == 1:
            return False

        params.append(id)
        update_sql = f"UPDATE api_interface SET {','.join(update_fields)} WHERE id = ?"

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
            cursor = conn.execute("DELETE FROM api_interface WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM api_interface WHERE id IN ({placeholders})", tuple(ids))
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def toggle_status(id: int) -> bool:
        with get_connection() as conn:
            conn.execute("UPDATE api_interface SET enabled = 1 - enabled WHERE id = ?", (id,))
            conn.commit()
        return True

    @staticmethod
    def get_enabled_interfaces():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM api_interface WHERE enabled = 1").fetchall()
        return [dict(row) for row in rows]
