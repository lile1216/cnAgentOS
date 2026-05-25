import hashlib
import secrets
import sqlite3

from app.models.db import get_connection

# 密码加密方法
def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()

# 用户对象类
class UserRepository:
    # 创建用户方法
    @staticmethod
    def create_user(username: str, password: str, role: str = 'user') -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)

        try:
            with get_connection() as conn:
                conn.execute(
                    "insert into user(username,password_hash,salt,role) values(?,?,?,?)",
                    (username, password_hash, salt.hex(), role)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_user_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "select id,username,password_hash,salt,role from user where username = ?",
                (username,)
            ).fetchone()
        return dict(row) if row else None

    # 验证用户名和密码的方法
    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        row = UserRepository.get_user_by_username(username)
        if not row:
            return False

        salt = bytes.fromhex(row["salt"])
        return _hash_password(password, salt) == row["password_hash"]

    # 获取用户列表（分页）
    @staticmethod
    def get_users(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "select id,username,role,create_at from user order by create_at desc limit ? offset ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    # 获取用户总数
    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("select count(*) as total from user").fetchone()
        return row["total"] if row else 0

    # 删除用户
    @staticmethod
    def delete_user(user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("delete from user where id = ?", (user_id,))
            conn.commit()
        return cursor.rowcount > 0

    # 批量删除用户
    @staticmethod
    def batch_delete_users(user_ids: list) -> int:
        if not user_ids:
            return 0
        
        placeholders = ",".join("?" * len(user_ids))
        with get_connection() as conn:
            cursor = conn.execute(f"delete from user where id in ({placeholders})", user_ids)
            conn.commit()
        return cursor.rowcount

    # 更新用户信息
    @staticmethod
    def update_user(user_id: int, username: str = None, password: str = None, role: str = None) -> bool:
        update_fields = []
        params = []
        
        if username:
            update_fields.append("username = ?")
            params.append(username)
        
        if password:
            salt = secrets.token_bytes(16)
            password_hash = _hash_password(password, salt)
            update_fields.append("password_hash = ?")
            update_fields.append("salt = ?")
            params.append(password_hash)
            params.append(salt.hex())
        
        if role:
            update_fields.append("role = ?")
            params.append(role)
        
        if not update_fields:
            return False
        
        params.append(user_id)
        update_sql = f"update user set {','.join(update_fields)} where id = ?"
        
        try:
            with get_connection() as conn:
                cursor = conn.execute(update_sql, params)
                conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    # 根据ID获取用户
    @staticmethod
    def get_user_by_id(user_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "select id,username,role,create_at from user where id = ?",
                (user_id,)
            ).fetchone()
        return dict(row) if row else None