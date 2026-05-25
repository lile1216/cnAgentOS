import tornado.web
import os

class WechatBasePageHandler(tornado.web.RequestHandler):
    """wechat_chat 页面处理基类"""
    
    def get_template_path(self):
        # 重写模板路径，指向子系统的 frontend 目录
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

class WechatHomePageHandler(WechatBasePageHandler):
    """主界面处理器"""
    def get(self):
        self.render("chat_main.html")

class WechatChatPageHandler(WechatBasePageHandler):
    """聊天页处理器"""
    def get(self):
        self.render("chat.html")

class WechatContactsPageHandler(WechatBasePageHandler):
    """通讯录页处理器"""
    def get(self):
        self.render("contacts.html")

class WechatAdminPageHandler(WechatBasePageHandler):
    """后台管理页处理器"""
    def get(self):
        self.render("admin.html")
