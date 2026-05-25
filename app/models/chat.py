import sqlite3
from app.models.db import get_connection

class ChatSessionRepository:
    @staticmethod
    def create(user_id: int, title: str = None, model_id: int = None, employee_id: int = None, session_type: str = "chat") -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_session(user_id, title, model_id, employee_id, session_type) VALUES(?, ?, ?, ?, ?)",
                (user_id, title, model_id, employee_id, session_type)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(session_id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM chat_session WHERE id = ?", (session_id,)).fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 50):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_session WHERE user_id = ? ORDER BY update_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def update(session_id: int, **kwargs):
        update_fields = []
        params = []
        allowed_fields = ['title', 'model_id', 'employee_id', 'session_type']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                update_fields.append(f"{key} = ?")
                params.append(value)
        if not update_fields:
            return False
        update_fields.append("update_at = datetime('now')")
        params.append(session_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE chat_session SET {','.join(update_fields)} WHERE id = ?", params)
            conn.commit()
        return True
    
    @staticmethod
    def delete(session_id: int):
        with get_connection() as conn:
            conn.execute("DELETE FROM chat_message WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM chat_session WHERE id = ?", (session_id,))
            conn.commit()
        return True

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_session ORDER BY update_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
            return [dict(row) for row in rows]

class ChatMessageRepository:
    @staticmethod
    def create(session_id: int, role: str, content: str, tokens: int = 0) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_message(session_id, role, content, tokens) VALUES(?, ?, ?, ?)",
                (session_id, role, content, tokens)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_session(session_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_message WHERE session_id = ? ORDER BY create_at ASC",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_session_id(session_id: int):
        return ChatMessageRepository.get_by_session(session_id)

    @staticmethod
    def get_recent_messages(session_id: int, limit: int = 20):
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM chat_message WHERE session_id = ? 
                   ORDER BY create_at DESC LIMIT ?""",
                (session_id, limit)
            ).fetchall()
            return [dict(row) for row in reversed(rows)]
    
    @staticmethod
    def delete_by_session(session_id: int):
        with get_connection() as conn:
            conn.execute("DELETE FROM chat_message WHERE session_id = ?", (session_id,))
            conn.commit()
        return True
