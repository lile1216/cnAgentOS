import os
os.chdir(r'c:\Users\47146\cnAgentOS')

import hashlib
import secrets
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "app.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()

default_users = [
    {"username": "Alice", "password": "test123", "role": "user"},
    {"username": "Bob", "password": "test123", "role": "user"},
    {"username": "Charlie", "password": "test123", "role": "user"},
    {"username": "David", "password": "test123", "role": "user"},
    {"username": "Eve", "password": "test123", "role": "user"},
]

with get_connection() as conn:
    for user in default_users:
        existing = conn.execute("SELECT id FROM user WHERE username = ?", (user["username"],)).fetchone()
        if not existing:
            salt = secrets.token_bytes(16)
            password_hash = hash_password(user["password"], salt)
            try:
                conn.execute(
                    "INSERT INTO user(username, password_hash, salt, role) VALUES(?, ?, ?, ?)",
                    (user["username"], password_hash, salt.hex(), user["role"])
                )
                print(f"Created user: {user['username']}")
            except sqlite3.IntegrityError:
                print(f"User {user['username']} already exists")
    conn.commit()

print("Default users initialization completed!")

# Verify
with get_connection() as conn:
    rows = conn.execute("SELECT username FROM user").fetchall()
    print("\nAll users in database:")
    for row in rows:
        print(f"  - {row['username']}")
