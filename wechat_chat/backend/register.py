import json
import tornado.web
from wechat_chat.backend.models import WechatUserRepository
from wechat_chat.backend.page_handlers import WechatBasePageHandler

class WechatRegisterHandler(WechatBasePageHandler):
    """子系统注册处理器"""
    
    def get(self):
        # 渲染全新开发的注册页面
        self.render("register.html")
    
    def post(self):
        try:
            data = json.loads(self.request.body)
            username = data.get("username", "").strip()
            password = data.get("password", "")
            confirm_password = data.get("confirm_password", "")
            
            if not username or not password:
                self.write({"code": 1, "msg": "用户名或密码不能为空"})
                return
                
            if len(password) < 6:
                self.write({"code": 1, "msg": "密码长度至少为6位"})
                return
                
            if password != confirm_password:
                self.write({"code": 1, "msg": "两次输入的密码不一致"})
                return
                
            if WechatUserRepository.get_user_by_username(username):
                self.write({"code": 1, "msg": "用户名已存在"})
                return
                
            if WechatUserRepository.create_user(username, password):
                self.write({"code": 0, "msg": "注册成功", "url": "/wechat-chat/login"})
            else:
                self.write({"code": 1, "msg": "注册失败，请稍后重试"})
        except Exception as e:
            self.write({"code": 1, "msg": f"注册异常: {str(e)}"})
