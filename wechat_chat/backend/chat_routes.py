import tornado.web
import os
from wechat_chat.backend.page_handlers import (
    WechatAdminPageHandler,
    WechatChatPageHandler,
    WechatContactsPageHandler,
    WechatHomePageHandler,
)
from wechat_chat.backend.login import WechatLoginHandler
from wechat_chat.backend.register import WechatRegisterHandler
from wechat_chat.backend.api_handlers import (
    WechatContactApiHandler,
    WechatChatApiHandler,
    WechatGroupApiHandler,
    WechatUploadApiHandler
)
from wechat_chat.backend.admin_handlers import (
    WechatGroupAdminApiHandler,
    WechatFileAdminApiHandler,
    WechatServerAdminApiHandler,
    WechatAIToolAdminApiHandler
)
from wechat_chat.backend.db import init_db

# 初始化子系统数据库
init_db()

WECHAT_CHAT_ROUTE_PREFIX = "/wechat-chat"

def get_chat_routes():
    """返回独立聊天子系统的路由配置"""
    # 获取子系统静态文件目录
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    
    return [
        # 页面路由
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/login", WechatLoginHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/register", WechatRegisterHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/home", WechatHomePageHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/chat", WechatChatPageHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/contacts", WechatContactsPageHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/admin", WechatAdminPageHandler),
        
        # API 路由
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/contacts", WechatContactApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/chat", WechatChatApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/groups", WechatGroupApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/upload", WechatUploadApiHandler),
        
        # 后台管理 API
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/admin/groups", WechatGroupAdminApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/admin/files", WechatFileAdminApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/admin/servers", WechatServerAdminApiHandler),
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/api/admin/ai-tools", WechatAIToolAdminApiHandler),
        
        # 子系统独立静态资源路由
        (rf"{WECHAT_CHAT_ROUTE_PREFIX}/static/(.*)", tornado.web.StaticFileHandler, {"path": static_path}),
    ]
