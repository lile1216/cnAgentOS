import json
import tornado.web
from wechat_chat.backend.models import WechatUserRepository
from wechat_chat.backend.page_handlers import WechatBasePageHandler

class WechatLoginHandler(WechatBasePageHandler):
    """子系统登录处理器"""
    
    def get(self):
        # 渲染全新开发的登录页面
        self.render("login.html")
    
    def post(self):
        try:
            data = json.loads(self.request.body)
            username = data.get("username", "").strip()
            password = data.get("password", "")
            
            if not username or not password:
                self.write({"code": 1, "msg": "用户名或密码不能为空"})
                return
                
            if WechatUserRepository.verify_user(username, password):
                # 设置独立系统的 Secure Cookie
                self.set_secure_cookie("wechat_username", username)
                self.write({"code": 0, "msg": "登录成功", "url": "/wechat-chat/home"})
            else:
                self.write({"code": 1, "msg": "用户名或密码错误"})
        except Exception as e:
            self.write({"code": 1, "msg": f"登录异常: {str(e)}"})
