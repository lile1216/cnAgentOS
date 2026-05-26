import tornado.web

from app.controllers.base import BaseHandler
from app.models.group import GroupChatRepository, GroupMemberRepository, GroupMessageRepository
from app.models.user import UserRepository


class AdminGroupHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/auth/user/login")
            return
        
        self.render("admin/group_admin.html", current_user=self.current_user)


class AdminGroupApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "list":
            self._get_all_groups()
        elif action == "members":
            self._get_group_members()
        elif action == "messages":
            self._get_group_messages()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "dissolve":
            self._dissolve_group()
        elif action == "ban_member":
            self._ban_member()
        elif action == "unban_member":
            self._unban_member()
        elif action == "send_announcement":
            self._send_announcement()
        elif action == "update_status":
            self._update_group_status()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_all_groups(self):
        with self.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT g.*, u.username as creator_name, COUNT(m.id) as member_count
                FROM group_chat g
                LEFT JOIN user u ON g.creator_id = u.id
                LEFT JOIN group_member m ON g.id = m.group_id
                GROUP BY g.id
                ORDER BY g.create_at DESC
                """
            ).fetchall()
        
        groups = [dict(row) for row in rows]
        self.write({"code": 0, "data": groups})
    
    def _get_group_members(self):
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        members = GroupMemberRepository.get_members(int(group_id))
        self.write({"code": 0, "data": members})
    
    def _get_group_messages(self):
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        messages = GroupMessageRepository.get_messages(int(group_id))
        self.write({"code": 0, "data": messages})
    
    def _dissolve_group(self):
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        success = GroupChatRepository.delete_group(int(group_id))
        if success:
            self.write({"code": 0, "msg": "群已解散"})
        else:
            self.write({"code": -1, "msg": "解散失败"})
    
    def _ban_member(self):
        group_id = self.get_argument("group_id", "")
        member_id = self.get_argument("member_id", "")
        
        if not group_id or not member_id:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        success = GroupMemberRepository.ban_member(int(group_id), int(member_id))
        if success:
            self.write({"code": 0, "msg": "封禁成功"})
        else:
            self.write({"code": -1, "msg": "封禁失败"})
    
    def _unban_member(self):
        group_id = self.get_argument("group_id", "")
        member_id = self.get_argument("member_id", "")
        
        if not group_id or not member_id:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        with self.get_db_connection() as conn:
            conn.execute(
                "UPDATE group_member SET is_banned = 0 WHERE group_id = ? AND user_id = ?",
                (int(group_id), int(member_id))
            )
            conn.commit()
        
        self.write({"code": 0, "msg": "解封成功"})
    
    def _send_announcement(self):
        group_id = self.get_argument("group_id", "")
        content = self.get_argument("content", "")
        
        if not group_id or not content.strip():
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        content = f"📢【系统公告】{content}"
        GroupMessageRepository.send_message(int(group_id), 0, content)
        
        self.write({"code": 0, "msg": "公告发布成功"})
    
    def _update_group_status(self):
        group_id = self.get_argument("group_id", "")
        status = self.get_argument("status", "")
        
        if not group_id or not status:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        success = GroupChatRepository.change_group_status(int(group_id), status)
        if success:
            self.write({"code": 0, "msg": "状态更新成功"})
        else:
            self.write({"code": -1, "msg": "更新失败"})
    
    def get_db_connection(self):
        from app.models.db import get_connection
        return get_connection()


class AdminFileHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/auth/user/login")
            return
        
        self.render("admin/file_admin.html", current_user=self.current_user)


class AdminFileApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "list":
            self._get_files()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "delete":
            self._delete_file()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_files(self):
        from app.models.group import ChatFileRepository
        files = ChatFileRepository.get_files_by_uploader(None)
        self.write({"code": 0, "data": files})
    
    def _delete_file(self):
        from app.models.group import ChatFileRepository
        
        file_id = self.get_argument("file_id", "")
        if not file_id:
            self.write({"code": -1, "msg": "缺少文件ID"})
            return
        
        success = ChatFileRepository.delete_file(int(file_id))
        if success:
            self.write({"code": 0, "msg": "删除成功"})
        else:
            self.write({"code": -1, "msg": "删除失败"})


class AdminServerHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/auth/user/login")
            return
        
        self.render("admin/server_admin.html", current_user=self.current_user)


class AdminServerApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "list":
            self._get_servers()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "create":
            self._create_server()
        elif action == "update":
            self._update_server()
        elif action == "toggle":
            self._toggle_server()
        elif action == "delete":
            self._delete_server()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_servers(self):
        from app.models.group import ChatServerRepository
        servers = ChatServerRepository.get_all_servers()
        self.write({"code": 0, "data": servers})
    
    def _create_server(self):
        from app.models.group import ChatServerRepository
        
        name = self.get_argument("name", "")
        host = self.get_argument("host", "")
        port = self.get_argument("port", 80)
        protocol = self.get_argument("protocol", "http")
        description = self.get_argument("description", "")
        
        if not name or not host:
            self.write({"code": -1, "msg": "缺少必填参数"})
            return
        
        success = ChatServerRepository.create_server(name, host, int(port), protocol, description)
        if success:
            self.write({"code": 0, "msg": "服务器创建成功"})
        else:
            self.write({"code": -1, "msg": "创建失败"})
    
    def _update_server(self):
        from app.models.group import ChatServerRepository
        
        server_id = self.get_argument("server_id", "")
        name = self.get_argument("name", "")
        host = self.get_argument("host", "")
        port = self.get_argument("port", "")
        protocol = self.get_argument("protocol", "")
        description = self.get_argument("description", "")
        
        if not server_id:
            self.write({"code": -1, "msg": "缺少服务器ID"})
            return
        
        success = ChatServerRepository.update_server(
            int(server_id), name if name else None, 
            host if host else None, 
            int(port) if port else None,
            protocol if protocol else None,
            description if description else None
        )
        
        if success:
            self.write({"code": 0, "msg": "服务器更新成功"})
        else:
            self.write({"code": -1, "msg": "更新失败"})
    
    def _toggle_server(self):
        from app.models.group import ChatServerRepository
        
        server_id = self.get_argument("server_id", "")
        if not server_id:
            self.write({"code": -1, "msg": "缺少服务器ID"})
            return
        
        success = ChatServerRepository.toggle_server(int(server_id))
        if success:
            self.write({"code": 0, "msg": "状态切换成功"})
        else:
            self.write({"code": -1, "msg": "切换失败"})
    
    def _delete_server(self):
        from app.models.group import ChatServerRepository
        
        server_id = self.get_argument("server_id", "")
        if not server_id:
            self.write({"code": -1, "msg": "缺少服务器ID"})
            return
        
        success = ChatServerRepository.delete_server(int(server_id))
        if success:
            self.write({"code": 0, "msg": "删除成功"})
        else:
            self.write({"code": -1, "msg": "删除失败"})