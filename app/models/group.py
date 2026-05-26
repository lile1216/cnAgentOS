import sqlite3
import hashlib
import os

from app.models.db import get_connection


class GroupChatRepository:
    @staticmethod
    def create_group(name: str, creator_id: int, description: str = "", avatar: str = "👥") -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO group_chat(name, avatar, description, creator_id) VALUES(?, ?, ?, ?)",
                (name, avatar, description, creator_id)
            )
            conn.commit()
            group_id = cursor.lastrowid
            
            conn.execute(
                "INSERT INTO group_member(group_id, user_id, role) VALUES(?, ?, ?)",
                (group_id, creator_id, "admin")
            )
            conn.commit()
        
        return group_id
    
    @staticmethod
    def get_group_by_id(group_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM group_chat WHERE id = ?",
                (group_id,)
            ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_groups_by_user(user_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT g.*, COUNT(m.id) as member_count
                FROM group_chat g
                JOIN group_member m ON g.id = m.group_id
                WHERE m.user_id = ? AND m.is_banned = 0
                GROUP BY g.id
                ORDER BY g.update_at DESC
                """,
                (user_id,)
            ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_group(group_id: int, name: str = None, description: str = None, avatar: str = None):
        update_fields = []
        params = []
        
        if name:
            update_fields.append("name = ?")
            params.append(name)
        if description:
            update_fields.append("description = ?")
            params.append(description)
        if avatar:
            update_fields.append("avatar = ?")
            params.append(avatar)
        
        if not update_fields:
            return False
        
        params.append(group_id)
        update_fields.append("update_at = datetime('now')")
        update_sql = f"UPDATE group_chat SET {','.join(update_fields)} WHERE id = ?"
        
        with get_connection() as conn:
            cursor = conn.execute(update_sql, params)
            conn.commit()
        
        return cursor.rowcount > 0
    
    @staticmethod
    def delete_group(group_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM group_chat WHERE id = ?", (group_id,))
            conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def change_group_status(group_id: int, status: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE group_chat SET status = ?, update_at = datetime('now') WHERE id = ?",
                (status, group_id)
            )
            conn.commit()
        return cursor.rowcount > 0


class GroupMemberRepository:
    @staticmethod
    def add_member(group_id: int, user_id: int, role: str = "member") -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO group_member(group_id, user_id, role) VALUES(?, ?, ?)",
                    (group_id, user_id, role)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    @staticmethod
    def add_members(group_id: int, user_ids: list) -> int:
        count = 0
        with get_connection() as conn:
            for user_id in user_ids:
                try:
                    conn.execute(
                        "INSERT INTO group_member(group_id, user_id, role) VALUES(?, ?, ?)",
                        (group_id, user_id, "member")
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
        return count
    
    @staticmethod
    def remove_member(group_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM group_member WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_members(group_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, m.role, m.join_time, m.is_muted, m.is_banned
                FROM group_member m
                JOIN user u ON m.user_id = u.id
                WHERE m.group_id = ?
                ORDER BY m.role DESC, m.join_time ASC
                """,
                (group_id,)
            ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_member(group_id: int, user_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM group_member WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update_member_role(group_id: int, user_id: int, role: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE group_member SET role = ? WHERE group_id = ? AND user_id = ?",
                (role, group_id, user_id)
            )
            conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def toggle_mute(group_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            conn.execute(
                "UPDATE group_member SET is_muted = 1 - is_muted WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            conn.commit()
        return True
    
    @staticmethod
    def ban_member(group_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE group_member SET is_banned = 1 WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            conn.commit()
        return cursor.rowcount > 0


class GroupMessageRepository:
    @staticmethod
    def send_message(group_id: int, from_user_id: int, content: str, message_type: str = "text", 
                    file_path: str = None, file_name: str = None, mentioned_users: str = None):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO group_message(group_id, from_user_id, content, message_type, 
                                        file_path, file_name, mentioned_users)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (group_id, from_user_id, content, message_type, file_path, file_name, mentioned_users)
            )
            conn.commit()
            
            conn.execute(
                "UPDATE group_chat SET update_at = datetime('now') WHERE id = ?",
                (group_id,)
            )
            conn.commit()
        return True
    
    @staticmethod
    def get_messages(group_id: int, limit: int = 100):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT gm.*, u.username as from_username
                FROM group_message gm
                JOIN user u ON gm.from_user_id = u.id
                WHERE gm.group_id = ?
                ORDER BY gm.send_time ASC
                LIMIT ?
                """,
                (group_id, limit)
            ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_unread_count(group_id: int, user_id: int) -> int:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) as count 
                FROM group_message gm
                LEFT JOIN group_member gm2 ON gm.group_id = gm2.group_id AND gm2.user_id = ?
                WHERE gm.group_id = ? AND gm.is_read = 0 AND gm.from_user_id != ?
                """,
                (user_id, group_id, user_id)
            ).fetchone()
        return row["count"] if row else 0


class ChatFileRepository:
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()
    
    @staticmethod
    def save_file(file_content: bytes, file_name: str, uploader_id: int = None) -> dict:
        file_hash = ChatFileRepository.calculate_file_hash(file_content)
        
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id, file_path FROM chat_file WHERE file_hash = ?",
                (file_hash,)
            ).fetchone()
            
            if existing:
                return {"id": existing["id"], "file_path": existing["file_path"], "is_new": False}
            
            upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, f"{file_hash}_{file_name}")
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            conn.execute(
                """
                INSERT INTO chat_file(file_hash, file_name, file_path, file_size, uploader_id)
                VALUES(?, ?, ?, ?, ?)
                """,
                (file_hash, file_name, file_path, len(file_content), uploader_id)
            )
            conn.commit()
            
            cursor = conn.execute("SELECT last_insert_rowid() as id")
            file_id = cursor.fetchone()["id"]
        
        return {"id": file_id, "file_path": file_path, "is_new": True}
    
    @staticmethod
    def get_file_by_id(file_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chat_file WHERE id = ?",
                (file_id,)
            ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_files_by_uploader(uploader_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_file WHERE uploader_id = ? ORDER BY upload_time DESC",
                (uploader_id,)
            ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def delete_file(file_id: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT file_path FROM chat_file WHERE id = ?",
                (file_id,)
            ).fetchone()
            
            if row:
                file_path = row["file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                cursor = conn.execute("DELETE FROM chat_file WHERE id = ?", (file_id,))
                conn.commit()
                return cursor.rowcount > 0
        
        return False


class ChatServerRepository:
    @staticmethod
    def create_server(name: str, host: str, port: int = 80, protocol: str = "http", 
                     description: str = "", is_default: bool = False):
        with get_connection() as conn:
            if is_default:
                conn.execute("UPDATE chat_server SET is_default = 0 WHERE is_default = 1")
            
            conn.execute(
                """
                INSERT INTO chat_server(name, host, port, protocol, description, is_default)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (name, host, port, protocol, description, 1 if is_default else 0)
            )
            conn.commit()
        return True
    
    @staticmethod
    def get_all_servers():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM chat_server ORDER BY weight DESC, id ASC").fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_default_server():
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM chat_server WHERE is_default = 1").fetchone()
            if not row:
                row = conn.execute("SELECT * FROM chat_server WHERE is_active = 1 ORDER BY weight DESC LIMIT 1").fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_active_servers():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM chat_server WHERE is_active = 1 ORDER BY weight DESC").fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def update_server(server_id: int, name: str = None, host: str = None, port: int = None, 
                     protocol: str = None, description: str = None, is_default: bool = None):
        with get_connection() as conn:
            update_fields = []
            params = []
            
            if name:
                update_fields.append("name = ?")
                params.append(name)
            if host:
                update_fields.append("host = ?")
                params.append(host)
            if port:
                update_fields.append("port = ?")
                params.append(port)
            if protocol:
                update_fields.append("protocol = ?")
                params.append(protocol)
            if description:
                update_fields.append("description = ?")
                params.append(description)
            if is_default is not None:
                if is_default:
                    conn.execute("UPDATE chat_server SET is_default = 0")
                update_fields.append("is_default = ?")
                params.append(1 if is_default else 0)
            
            if update_fields:
                params.append(server_id)
                update_fields.append("update_at = datetime('now')")
                update_sql = f"UPDATE chat_server SET {','.join(update_fields)} WHERE id = ?"
                conn.execute(update_sql, params)
                conn.commit()
        
        return True
    
    @staticmethod
    def toggle_server(server_id: int) -> bool:
        with get_connection() as conn:
            conn.execute(
                "UPDATE chat_server SET is_active = 1 - is_active WHERE id = ?",
                (server_id,)
            )
            conn.commit()
        return True
    
    @staticmethod
    def delete_server(server_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM chat_server WHERE id = ?", (server_id,))
            conn.commit()
        return cursor.rowcount > 0