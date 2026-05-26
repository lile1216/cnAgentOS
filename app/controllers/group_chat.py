import tornado.web
import json

from app.models.group import GroupChatRepository, GroupMemberRepository, GroupMessageRepository
from app.models.user import UserRepository
from app.models.friendship import FriendshipRepository
from app.models.digital_employee import DigitalEmployeeManager


class GroupChatApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "list":
            self._get_groups()
        elif action == "members":
            self._get_members()
        elif action == "messages":
            self._get_messages()
        elif action == "employees":
            self._get_employees()
        elif action == "employee_chat":
            self._employee_chat()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "create":
            self._create_group()
        elif action == "add_member":
            self._add_member()
        elif action == "remove_member":
            self._remove_member()
        elif action == "send":
            self._send_message()
        elif action == "dissolve":
            self._dissolve_group()
        elif action == "ban_member":
            self._ban_member()
        elif action == "send_announcement":
            self._send_announcement()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_groups(self):
        user_id = self.get_current_user_id()
        if not user_id:
            user_id = 1
        
        groups = GroupChatRepository.get_groups_by_user(user_id)
        self.write({"code": 0, "data": groups})
    
    def _get_members(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        members = GroupMemberRepository.get_members(int(group_id))
        self.write({"code": 0, "data": members})
    
    def _get_messages(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        messages = GroupMessageRepository.get_messages(int(group_id))
        self.write({"code": 0, "data": messages})
    
    def _get_employees(self):
        employees = DigitalEmployeeManager.list_employees()
        employee_list = []
        for name in employees:
            emp = DigitalEmployeeManager.get_employee(name)
            employee_list.append({
                "name": emp.name,
                "avatar": emp.avatar
            })
        self.write({"code": 0, "data": employee_list})
    
    def _employee_chat(self):
        employee_name = self.get_argument("employee_name", "")
        content = self.get_argument("content", "")
        
        if not employee_name or not content.strip():
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        employee = DigitalEmployeeManager.get_employee(employee_name)
        if not employee:
            self.write({"code": -1, "msg": "数字员工不存在"})
            return
        
        response = employee.respond(content.strip())
        self.write({"code": 0, "data": {
            "employee_name": employee_name,
            "avatar": employee.avatar,
            "response": response
        }})
    
    def _create_group(self):
        user_id = self.get_current_user_id()
        if not user_id:
            user_id = 1
        
        name = self.get_argument("name", "")
        friend_ids = self.get_argument("friend_ids", "")
        employee_name = self.get_argument("employee_name", "")
        
        if not name:
            self.write({"code": -1, "msg": "请输入群名称"})
            return
        
        group_id = GroupChatRepository.create_group(name, user_id)
        
        if friend_ids:
            try:
                friend_ids_list = json.loads(friend_ids)
                GroupMemberRepository.add_members(group_id, friend_ids_list)
            except:
                pass
        
        self.write({"code": 0, "msg": "群聊创建成功", "data": {"group_id": group_id}})
    
    def _add_member(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        friend_ids = self.get_argument("friend_ids", "")
        
        if not group_id or not friend_ids:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        try:
            friend_ids_list = json.loads(friend_ids)
            count = GroupMemberRepository.add_members(int(group_id), friend_ids_list)
            self.write({"code": 0, "msg": f"成功添加{count}位成员"})
        except Exception as e:
            self.write({"code": -1, "msg": str(e)})
    
    def _remove_member(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        member_id = self.get_argument("member_id", "")
        
        if not group_id or not member_id:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        member = GroupMemberRepository.get_member(int(group_id), int(member_id))
        if not member:
            self.write({"code": -1, "msg": "成员不存在"})
            return
        
        if member["role"] == "admin":
            self.write({"code": -1, "msg": "不能移除管理员"})
            return
        
        success = GroupMemberRepository.remove_member(int(group_id), int(member_id))
        if success:
            self.write({"code": 0, "msg": "移除成功"})
        else:
            self.write({"code": -1, "msg": "移除失败"})
    
    def _send_message(self):
        user_id = self.get_current_user_id()
        if not user_id:
            user_id = 1
        
        group_id = self.get_argument("group_id", "")
        content = self.get_argument("content", "")
        
        if not group_id or not content.strip():
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        member = GroupMemberRepository.get_member(int(group_id), user_id)
        if not member or member["is_banned"]:
            GroupMemberRepository.add_member(int(group_id), user_id)
            member = {"is_banned": False}
        
        mentioned_users = None
        employee_name = None
        
        if "@" in content:
            employees = DigitalEmployeeManager.list_employees()
            for emp_name in employees:
                if f"@{emp_name}" in content:
                    employee_name = emp_name
                    content = content.replace(f"@{emp_name}", "")
                    break
        
        GroupMessageRepository.send_message(
            int(group_id), user_id, content.strip(),
            mentioned_users=mentioned_users
        )
        
        if employee_name:
            employee = DigitalEmployeeManager.get_employee(employee_name)
            if employee:
                response = employee.respond(content.strip())
                GroupMessageRepository.send_message(
                    int(group_id), 0, response,
                    mentioned_users=None
                )
        
        self.write({"code": 0, "msg": "消息发送成功"})
    
    def _dissolve_group(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        if not group_id:
            self.write({"code": -1, "msg": "缺少群ID"})
            return
        
        group = GroupChatRepository.get_group_by_id(int(group_id))
        if not group:
            self.write({"code": -1, "msg": "群不存在"})
            return
        
        if group["creator_id"] != user_id:
            self.write({"code": -1, "msg": "只有群主才能解散群"})
            return
        
        success = GroupChatRepository.delete_group(int(group_id))
        if success:
            self.write({"code": 0, "msg": "群已解散"})
        else:
            self.write({"code": -1, "msg": "解散失败"})
    
    def _ban_member(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        member_id = self.get_argument("member_id", "")
        
        if not group_id or not member_id:
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        member = GroupMemberRepository.get_member(int(group_id), int(member_id))
        if not member:
            self.write({"code": -1, "msg": "成员不存在"})
            return
        
        if member["role"] == "admin":
            self.write({"code": -1, "msg": "不能封禁管理员"})
            return
        
        success = GroupMemberRepository.ban_member(int(group_id), int(member_id))
        if success:
            self.write({"code": 0, "msg": "封禁成功"})
        else:
            self.write({"code": -1, "msg": "封禁失败"})
    
    def _send_announcement(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        group_id = self.get_argument("group_id", "")
        content = self.get_argument("content", "")
        
        if not group_id or not content.strip():
            self.write({"code": -1, "msg": "缺少参数"})
            return
        
        member = GroupMemberRepository.get_member(int(group_id), user_id)
        if not member or member["role"] != "admin":
            self.write({"code": -1, "msg": "只有管理员才能发布公告"})
            return
        
        content = f"📢【群公告】{content}"
        GroupMessageRepository.send_message(int(group_id), user_id, content)
        
        self.write({"code": 0, "msg": "公告发布成功"})
    
    def get_current_user_id(self):
        username = self.get_current_user()
        if not username:
            return None
        user = UserRepository.get_user_by_username(username.decode("utf-8"))
        return user["id"] if user else None
