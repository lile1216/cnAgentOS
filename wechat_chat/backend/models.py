import hashlib
import secrets
import sqlite3
from wechat_chat.backend.db import get_connection

def _hash_password(password: str, salt: bytes) -> str:
    """密码加密 (保持与原系统风格一致)"""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()

class WechatUserRepository:
    """聊天子系统用户仓库 (独立于原系统)"""
    
    @staticmethod
    def create_user(username: str, password: str, nickname: str = None) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        nickname = nickname or username

        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO wechat_user(username, password_hash, salt, nickname) VALUES(?,?,?,?)",
                    (username, password_hash, salt.hex(), nickname)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_user_by_username(username: str):
        """根据用户名获取用户信息"""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt, nickname, avatar FROM wechat_user WHERE username = ?",
                (username,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        """验证用户名和密码"""
        user = WechatUserRepository.get_user_by_username(username)
        if not user:
            return False

        salt = bytes.fromhex(user["salt"])
        return _hash_password(password, salt) == user["password_hash"]

class WechatFriendRepository:
    """好友关系仓库"""
    
    @staticmethod
    def get_friends(user_id: int):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT u.id, u.username, u.nickname, u.avatar, f.remark 
                FROM wechat_friend f 
                JOIN wechat_user u ON f.friend_id = u.id 
                WHERE f.user_id = ?
            """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def add_friend(user_id: int, friend_id: int) -> bool:
        try:
            with get_connection() as conn:
                # 双向添加好友
                conn.execute("INSERT INTO wechat_friend(user_id, friend_id) VALUES(?,?)", (user_id, friend_id))
                conn.execute("INSERT INTO wechat_friend(user_id, friend_id) VALUES(?,?)", (friend_id, user_id))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

class WechatFriendRequestRepository:
    """好友申请仓库"""
    
    @staticmethod
    def create_request(from_id: int, to_id: int, message: str = "") -> bool:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO wechat_friend_request(from_user_id, to_user_id, message) VALUES(?,?,?)",
                (from_id, to_id, message)
            )
            conn.commit()
        return True

    @staticmethod
    def get_pending_requests(user_id: int):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, u.username, u.nickname, u.avatar 
                FROM wechat_friend_request r 
                JOIN wechat_user u ON r.from_user_id = u.id 
                WHERE r.to_user_id = ? AND r.status = 0
            """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update_status(request_id: int, status: int) -> bool:
        with get_connection() as conn:
            conn.execute("UPDATE wechat_friend_request SET status = ? WHERE id = ?", (status, request_id))
            conn.commit()
        return True

class WechatGroupRepository:
    """群组仓库"""
    
    @staticmethod
    def create_group(name: str, owner_id: int, member_ids: list) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO wechat_group(name, owner_id) VALUES(?,?)",
                (name, owner_id)
            )
            group_id = cursor.lastrowid
            
            # 添加成员 (包括创建者)
            all_members = list(set(member_ids + [owner_id]))
            for uid in all_members:
                role = 'owner' if uid == owner_id else 'member'
                conn.execute(
                    "INSERT INTO wechat_group_member(group_id, user_id, role) VALUES(?,?,?)",
                    (group_id, uid, role)
                )
            conn.commit()
            return group_id

    @staticmethod
    def get_user_groups(user_id: int):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT g.* FROM wechat_group g 
                JOIN wechat_group_member m ON g.id = m.group_id 
                WHERE m.user_id = ?
            """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

class WechatMessageRepository:
    """消息仓库"""
    
    @staticmethod
    def save_message(sender_id: int, target_id: int, chat_type: str, content: str, content_type: str = 'text'):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO wechat_message(sender_id, target_id, chat_type, content, content_type) 
                VALUES(?,?,?,?,?)
            """, (sender_id, target_id, chat_type, content, content_type))
            conn.commit()
        return True

    @staticmethod
    def get_messages(user_id: int, target_id: int, chat_type: str, limit: int = 50):
        with get_connection() as conn:
            if chat_type == 'private':
                rows = conn.execute("""
                    SELECT * FROM wechat_message 
                    WHERE chat_type = 'private' 
                    AND ((sender_id = ? AND target_id = ?) OR (sender_id = ? AND target_id = ?)) 
                    ORDER BY create_at DESC LIMIT ?
                """, (user_id, target_id, target_id, user_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM wechat_message 
                    WHERE chat_type = 'group' AND target_id = ? 
                    ORDER BY create_at DESC LIMIT ?
                """, (target_id, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]
