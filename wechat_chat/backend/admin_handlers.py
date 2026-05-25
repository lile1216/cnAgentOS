import json
import tornado.web
from wechat_chat.backend.api_handlers import WechatBaseApiHandler
from wechat_chat.backend.db import get_connection
from wechat_chat.backend.file_service import WechatFileService
from wechat_chat.backend.models import WechatMessageRepository

class WechatGroupAdminApiHandler(WechatBaseApiHandler):
    """后台群组管理 API"""
    
    def get(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT g.*, u.nickname as owner_name FROM wechat_group g JOIN wechat_user u ON g.owner_id = u.id").fetchall()
        self.write({"code": 0, "data": [dict(row) for row in rows]})

    def post(self):
        data = json.loads(self.request.body)
        action = data.get("action")
        group_id = data.get("group_id")
        
        with get_connection() as conn:
            if action == "dissolve":
                conn.execute("UPDATE wechat_group SET status = 0 WHERE id = ?", (group_id,))
            elif action == "mute":
                mute_status = data.get("status", 1)
                conn.execute("UPDATE wechat_group SET is_muted = ? WHERE id = ?", (mute_status, group_id))
            elif action == "announce":
                content = data.get("content")
                conn.execute("UPDATE wechat_group SET announcement = ? WHERE id = ?", (content, group_id))
                # 记录为系统公告消息
                ai_user = conn.execute("SELECT id FROM wechat_user WHERE username = 'chuannong_helper'").fetchone()
                if ai_user:
                    WechatMessageRepository.save_message(ai_user['id'], group_id, 'group', f"【群公告】: {content}")
            conn.commit()
        self.write({"code": 0, "msg": "操作成功"})

class WechatFileAdminApiHandler(WechatBaseApiHandler):
    """后台文件管理 API"""
    
    def get(self):
        files = WechatFileService.get_all_files()
        self.write({"code": 0, "data": files})

    def delete(self):
        file_id = self.get_argument("id")
        if WechatFileService.delete_file(file_id):
            self.write({"code": 0, "msg": "删除成功"})
        else:
            self.write({"code": 1, "msg": "删除失败"})

class WechatServerAdminApiHandler(WechatBaseApiHandler):
    """后台服务器管理 API"""
    
    def get(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM wechat_server").fetchall()
        self.write({"code": 0, "data": [dict(row) for row in rows]})

    def post(self):
        data = json.loads(self.request.body)
        name = data.get("name")
        host = data.get("host")
        port = data.get("port")
        
        with get_connection() as conn:
            conn.execute("INSERT INTO wechat_server (name, host, port) VALUES (?, ?, ?)", (name, host, port))
            conn.commit()
        self.write({"code": 0, "msg": "添加成功"})

class WechatAIToolAdminApiHandler(WechatBaseApiHandler):
    """后台 AI 工具管理 API"""
    
    def get(self):
        with get_connection() as conn:
            tools = conn.execute("SELECT * FROM wechat_ai_tool").fetchall()
            bindings = conn.execute("""
                SELECT b.*, u.nickname as employee_name, t.name as tool_name 
                FROM wechat_ai_tool_binding b
                JOIN wechat_user u ON b.employee_id = u.id
                JOIN wechat_ai_tool t ON b.tool_id = t.id
            """).fetchall()
        self.write({"code": 0, "data": {"tools": [dict(t) for t in tools], "bindings": [dict(b) for b in bindings]}})

    def post(self):
        data = json.loads(self.request.body)
        action = data.get("action")
        
        with get_connection() as conn:
            if action == "add_tool":
                conn.execute("INSERT INTO wechat_ai_tool (name, tool_type, config) VALUES (?, ?, ?)", 
                            (data.get("name"), data.get("type"), data.get("config")))
            elif action == "bind":
                conn.execute("INSERT OR REPLACE INTO wechat_ai_tool_binding (employee_id, tool_id) VALUES (?, ?)",
                            (data.get("employee_id"), data.get("tool_id")))
            conn.commit()
        self.write({"code": 0, "msg": "操作成功"})
