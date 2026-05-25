import tornado.web
import json

from app.controllers.base import BaseHandler
from app.models.user import UserRepository

class LoginHandler(BaseHandler):
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("login.html", xsrf_token=xsrf_token)
    
    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        
        if not username or not password:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "用户名或密码不能为空"}))
            return
        
        if UserRepository.verify_user(username, password):
            self.set_secure_cookie("username", username)
            user = UserRepository.get_user_by_username(username)
            if user and user["role"] == "admin":
                self.write(json.dumps({"code": 0, "msg": "登录成功", "url": "/admin"}))
            else:
                self.write(json.dumps({"code": 0, "msg": "登录成功", "url": "/chat"}))
        else:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "用户名或密码错误"}))

class UserLoginHandler(BaseHandler):
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("user_login.html", xsrf_token=xsrf_token)
    
    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        
        if not username or not password:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "用户名或密码不能为空"}))
            return
        
        if UserRepository.verify_user(username, password):
            self.set_secure_cookie("username", username)
            user = UserRepository.get_user_by_username(username)
            if user and user["role"] == "admin":
                self.write(json.dumps({"code": 0, "msg": "登录成功", "url": "/admin"}))
            else:
                self.write(json.dumps({"code": 0, "msg": "登录成功", "url": "/chat"}))
        else:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "用户名或密码错误"}))

class RegisterHandler(BaseHandler):
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("register.html", xsrf_token=xsrf_token)
    
    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        confirm_password = self.get_body_argument("confirm_password", "")
        
        if not username or not password:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "用户名或密码不能为空"}))
            return
        
        if len(username) < 3:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "用户名至少3个字符"}))
            return
        
        if len(password) < 6:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "密码至少6个字符"}))
            return
        
        if password != confirm_password:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "两次密码不一致"}))
            return
        
        if UserRepository.get_user_by_username(username):
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "用户名已存在"}))
            return
        
        if UserRepository.create_user(username, password, "user"):
            self.write(json.dumps({"code": 0, "msg": "注册成功", "url": "/auth/user/login"}))
        else:
            self.set_status(500)
            self.write(json.dumps({"code": 1, "msg": "注册失败，请稍后重试"}))

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/auth/user/login")
