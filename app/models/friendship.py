import sqlite3

from app.models.db import get_connection
from app.models.user import UserRepository

class FriendshipRepository:
    @staticmethod
    def send_friend_request(user_id: int, friend_username: str):
        friend_user = UserRepository.get_user_by_username(friend_username)
        if not friend_user:
            return {"success": False, "msg": "用户不存在"}
        
        friend_id = friend_user["id"]
        
        if user_id == friend_id:
            return {"success": False, "msg": "不能添加自己为好友"}
        
        try:
            with get_connection() as conn:
                existing = conn.execute(
                    "SELECT status FROM friendship WHERE user_id=? AND friend_id=?",
                    (user_id, friend_id)
                ).fetchone()
                
                if existing:
                    if existing["status"] == "accepted":
                        return {"success": False, "msg": "已经是好友"}
                
                conn.execute(
                    "INSERT OR REPLACE INTO friendship(user_id, friend_id, status) VALUES(?, ?, ?)",
                    (user_id, friend_id, "accepted")
                )
                conn.execute(
                    "INSERT OR REPLACE INTO friendship(user_id, friend_id, status) VALUES(?, ?, ?)",
                    (friend_id, user_id, "accepted")
                )
                conn.commit()
            
            return {"success": True, "msg": "添加好友成功"}
        
        except sqlite3.Error as e:
            return {"success": False, "msg": f"操作失败: {str(e)}"}
    
    @staticmethod
    def accept_friend_request(user_id: int, friend_id: int):
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE friendship SET status = 'accepted', update_at = datetime('now') WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                    (friend_id, user_id)
                )
                conn.commit()
            
            if cursor.rowcount > 0:
                with get_connection() as conn:
                    try:
                        conn.execute(
                            "INSERT INTO friendship(user_id, friend_id, status) VALUES(?, ?, ?)",
                            (user_id, friend_id, "accepted")
                        )
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                
                return {"success": True, "msg": "已通过好友请求"}
            else:
                return {"success": False, "msg": "好友请求不存在或已处理"}
        
        except sqlite3.Error as e:
            return {"success": False, "msg": f"操作失败: {str(e)}"}
    
    @staticmethod
    def reject_friend_request(user_id: int, friend_id: int):
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM friendship WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                    (friend_id, user_id)
                )
                conn.commit()
            
            if cursor.rowcount > 0:
                return {"success": True, "msg": "已拒绝好友请求"}
            else:
                return {"success": False, "msg": "好友请求不存在或已处理"}
        
        except sqlite3.Error as e:
            return {"success": False, "msg": f"操作失败: {str(e)}"}
    
    @staticmethod
    def get_friends(user_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.create_at 
                FROM friendship f
                JOIN user u ON f.friend_id = u.id
                WHERE f.user_id = ? AND f.status = 'accepted'
                ORDER BY f.update_at DESC
                """,
                (user_id,)
            ).fetchall()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_pending_requests(user_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.create_at, f.create_at as request_time
                FROM friendship f
                JOIN user u ON f.user_id = u.id
                WHERE f.friend_id = ? AND f.status = 'pending'
                ORDER BY f.create_at DESC
                """,
                (user_id,)
            ).fetchall()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def is_friend(user_id: int, friend_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM friendship WHERE user_id = ? AND friend_id = ? AND status = 'accepted'",
                (user_id, friend_id)
            ).fetchone()
        
        return row is not None


class PrivateMessageRepository:
    @staticmethod
    def send_message(from_user_id: int, to_user_id: int, content: str):
        if not content.strip():
            return {"success": False, "msg": "消息内容不能为空"}
        
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO private_message(from_user_id, to_user_id, content) VALUES(?, ?, ?)",
                    (from_user_id, to_user_id, content.strip())
                )
                conn.commit()
            
            return {"success": True, "msg": "消息发送成功"}
        
        except sqlite3.Error as e:
            return {"success": False, "msg": f"发送失败: {str(e)}"}
    
    @staticmethod
    def get_messages(user_id: int, friend_id: int, limit: int = 50):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT pm.id, pm.from_user_id, pm.to_user_id, pm.content, pm.is_read, pm.send_time,
                       u1.username as from_username, u2.username as to_username
                FROM private_message pm
                JOIN user u1 ON pm.from_user_id = u1.id
                JOIN user u2 ON pm.to_user_id = u2.id
                WHERE (pm.from_user_id = ? AND pm.to_user_id = ?) OR (pm.from_user_id = ? AND pm.to_user_id = ?)
                ORDER BY pm.send_time ASC
                LIMIT ?
                """,
                (user_id, friend_id, friend_id, user_id, limit)
            ).fetchall()
        
        messages = [dict(row) for row in rows]
        
        with get_connection() as conn:
            conn.execute(
                "UPDATE private_message SET is_read = 1 WHERE to_user_id = ? AND from_user_id = ? AND is_read = 0",
                (user_id, friend_id)
            )
            conn.commit()
        
        return messages
    
    @staticmethod
    def get_unread_count(user_id: int, friend_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM private_message WHERE to_user_id = ? AND from_user_id = ? AND is_read = 0",
                (user_id, friend_id)
            ).fetchone()
        
        return row["count"] if row else 0
    
    @staticmethod
    def get_conversations(user_id: int):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    CASE WHEN pm.from_user_id = ? THEN pm.to_user_id ELSE pm.from_user_id END as other_user_id,
                    u.username,
                    MAX(pm.send_time) as last_time,
                    COUNT(CASE WHEN pm.to_user_id = ? AND pm.is_read = 0 THEN 1 END) as unread_count,
                    SUBSTRING(MAX(pm.send_time || pm.content), 20) as last_content
                FROM private_message pm
                JOIN user u ON (pm.from_user_id = ? AND pm.to_user_id = u.id) OR (pm.to_user_id = ? AND pm.from_user_id = u.id)
                WHERE pm.from_user_id = ? OR pm.to_user_id = ?
                GROUP BY other_user_id
                ORDER BY last_time DESC
                """,
                (user_id, user_id, user_id, user_id, user_id, user_id)
            ).fetchall()
        
        return [dict(row) for row in rows]
