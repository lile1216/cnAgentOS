import sqlite3
from app.models.db import get_connection

class DigitalEmployeeRepository:
    @staticmethod
    def create(name: str, alias: str, category: str = "AI", description: str = "",
               prompt: str = None, model_id: int = None, api_interface_id: int = None,
               avatar: str = "🤖", welcome_msg: str = "", enabled: bool = True) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO digital_employee(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, 1 if enabled else 0)
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
                "SELECT * FROM digital_employee ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM digital_employee").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employee WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_alias(alias: str):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employee WHERE alias = ? AND enabled = 1", (alias,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, name: str = None, alias: str = None, category: str = None,
               description: str = None, prompt: str = None, model_id: int = None,
               api_interface_id: int = None, avatar: str = None, welcome_msg: str = None,
               enabled: bool = None) -> bool:
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if alias:
            update_fields.append("alias = ?")
            params.append(alias)
        if category:
            update_fields.append("category = ?")
            params.append(category)
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
        if prompt is not None:
            update_fields.append("prompt = ?")
            params.append(prompt)
        if model_id is not None:
            update_fields.append("model_id = ?")
            params.append(model_id)
        if api_interface_id is not None:
            update_fields.append("api_interface_id = ?")
            params.append(api_interface_id)
        if avatar is not None:
            update_fields.append("avatar = ?")
            params.append(avatar)
        if welcome_msg is not None:
            update_fields.append("welcome_msg = ?")
            params.append(welcome_msg)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        update_fields.append("update_at = datetime('now')")

        if len(update_fields) == 1:
            return False

        params.append(id)
        update_sql = f"UPDATE digital_employee SET {','.join(update_fields)} WHERE id = ?"

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
            cursor = conn.execute("DELETE FROM digital_employee WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM digital_employee WHERE id IN ({placeholders})", tuple(ids))
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def toggle_status(id: int) -> bool:
        with get_connection() as conn:
            conn.execute("UPDATE digital_employee SET enabled = 1 - enabled WHERE id = ?", (id,))
            conn.commit()
        return True

    @staticmethod
    def get_enabled_employees():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM digital_employee WHERE enabled = 1").fetchall()
        return [dict(row) for row in rows]
