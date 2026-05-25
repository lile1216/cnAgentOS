import os
import sqlite3

def get_db_path():
    """获取子系统独立数据库路径"""
    # 确保目录存在
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return os.path.join(db_dir, "wechat.db")

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化子系统数据库表"""
    with get_connection() as conn:
        # 创建独立的聊天用户表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nickname TEXT,
                avatar TEXT,
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        
        # 预置 AI 助手虚拟账号
        ai_helpers = [
            ('chuannong_helper', '川农小助手', '🎓'),
            ('weather_helper', '天气小助手', '🌤️'),
            ('soup_helper', '毒鸡汤助手', '🍲')
        ]
        for username, nickname, avatar in ai_helpers:
            conn.execute("""
                INSERT OR IGNORE INTO wechat_user(username, password_hash, salt, nickname, avatar)
                VALUES(?, 'AI_BOT', 'AI_SALT', ?, ?)
            """, (username, nickname, avatar))
        
        # 好友关系表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_friend (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                remark TEXT,
                status INTEGER DEFAULT 1, -- 1: 正常, 0: 黑名单
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                UNIQUE(user_id, friend_id),
                FOREIGN KEY(user_id) REFERENCES wechat_user(id),
                FOREIGN KEY(friend_id) REFERENCES wechat_user(id)
            )
        """)
        
        # 好友申请表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_friend_request (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                message TEXT,
                status INTEGER DEFAULT 0, -- 0: 待处理, 1: 已同意, 2: 已拒绝
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(from_user_id) REFERENCES wechat_user(id),
                FOREIGN KEY(to_user_id) REFERENCES wechat_user(id)
            )
        """)
        
        # 群组表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                announcement TEXT,
                avatar TEXT,
                status INTEGER DEFAULT 1, -- 1: 正常, 0: 解散/封禁
                is_muted INTEGER DEFAULT 0, -- 0: 正常发言, 1: 全体禁言
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(owner_id) REFERENCES wechat_user(id)
            )
        """)
        
        # 文件索引表 (实现 MD5 去重)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_file_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                md5 TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                original_name TEXT,
                file_size INTEGER,
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        
        # 聊天服务器配置表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_server (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status INTEGER DEFAULT 1, -- 1: 启用, 0: 禁用
                is_current INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        
        # AI 工具定义表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_ai_tool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                tool_type TEXT NOT NULL, -- 'api', 'function', 'script'
                config TEXT, -- JSON 格式配置
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        
        # AI 工具与数字员工绑定表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_ai_tool_binding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                tool_id INTEGER NOT NULL,
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                UNIQUE(employee_id, tool_id),
                FOREIGN KEY(employee_id) REFERENCES wechat_user(id),
                FOREIGN KEY(tool_id) REFERENCES wechat_ai_tool(id)
            )
        """)
        
        # 群成员表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_group_member (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member', -- owner, admin, member
                nickname_in_group TEXT,
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                UNIQUE(group_id, user_id),
                FOREIGN KEY(group_id) REFERENCES wechat_group(id),
                FOREIGN KEY(user_id) REFERENCES wechat_user(id)
            )
        """)
        
        # 消息表 (1v1 和 群聊)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wechat_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL, -- 好友ID 或 群组ID
                chat_type TEXT NOT NULL, -- 'private', 'group'
                content_type TEXT DEFAULT 'text', -- 'text', 'image', 'file'
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(sender_id) REFERENCES wechat_user(id)
            )
        """)
        
        conn.commit()
