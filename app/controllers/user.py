import json
import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository

class UserListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("user_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class UserApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page = 1
            page_size = 20
        
        users = UserRepository.get_users(page, page_size)
        total = UserRepository.get_total_count()
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": users
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_user()
        elif action == "edit":
            self._edit_user()
        elif action == "delete":
            self._delete_user()
        elif action == "batchDelete":
            self._batch_delete_users()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_user(self):
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "")
        role = self.get_body_argument("role", "user")
        
        if not username or not password:
            self.write(json.dumps({"code": 1, "msg": "用户名和密码不能为空"}))
            return
        
        if username == "admin":
            self.write(json.dumps({"code": 1, "msg": "不能创建名为admin的用户"}))
            return
        
        if UserRepository.create_user(username, password, role):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "用户名已存在"}))

    def _edit_user(self):
        user_id = self.get_body_argument("id", "")
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "")
        role = self.get_body_argument("role", "")
        
        if not user_id:
            self.write(json.dumps({"code": 1, "msg": "用户ID不能为空"}))
            return
        
        try:
            user_id = int(user_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的用户ID"}))
            return
        
        user = UserRepository.get_user_by_id(user_id)
        if not user:
            self.write(json.dumps({"code": 1, "msg": "用户不存在"}))
            return
        
        # 如果是admin用户，只能修改密码
        if user["username"] == "admin":
            if username and username != "admin":
                self.write(json.dumps({"code": 1, "msg": "超级管理员用户名不能修改"}))
                return
            if role and role != "admin":
                self.write(json.dumps({"code": 1, "msg": "超级管理员角色不能修改"}))
                return
            
            # 如果提供了密码，则修改密码
            if password:
                if UserRepository.update_user(user_id, password=password):
                    self.write(json.dumps({"code": 0, "msg": "密码修改成功"}))
                else:
                    self.write(json.dumps({"code": 1, "msg": "修改失败"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "超级管理员只能修改密码"}))
            return
        
        # 普通用户可以修改用户名、密码、角色
        update_params = {}
        if username:
            update_params["username"] = username
        if password:
            update_params["password"] = password
        if role:
            update_params["role"] = role
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if UserRepository.update_user(user_id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败，用户名可能已存在"}))

    def _delete_user(self):
        user_id = self.get_body_argument("id", "")
        
        if not user_id:
            self.write(json.dumps({"code": 1, "msg": "用户ID不能为空"}))
            return
        
        try:
            user_id = int(user_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的用户ID"}))
            return
        
        user = UserRepository.get_user_by_id(user_id)
        if not user:
            self.write(json.dumps({"code": 1, "msg": "用户不存在"}))
            return
        
        if user["username"] == "admin":
            self.write(json.dumps({"code": 1, "msg": "超级管理员不能删除"}))
            return
        
        if UserRepository.delete_user(user_id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete_users(self):
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的用户"}))
            return
        
        try:
            user_ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的用户ID列表"}))
            return
        
        for user_id in user_ids:
            user = UserRepository.get_user_by_id(user_id)
            if user and user["username"] == "admin":
                self.write(json.dumps({"code": 1, "msg": "不能删除超级管理员"}))
                return
        
        deleted_count = UserRepository.batch_delete_users(user_ids)
        self.write(json.dumps({
            "code": 0,
            "msg": f"成功删除 {deleted_count} 条记录"
        }))

class UserInfoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = self.get_argument("id", "")
        
        if not user_id:
            self.write(json.dumps({"code": 1, "msg": "用户ID不能为空"}))
            return
        
        try:
            user_id = int(user_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的用户ID"}))
            return
        
        user = UserRepository.get_user_by_id(user_id)
        if user:
            self.write(json.dumps({"code": 0, "msg": "success", "data": user}))
        else:
            self.write(json.dumps({"code": 1, "msg": "用户不存在"}))
