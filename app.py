import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
import os

from app.models.db import init_db, init_scout_sources, init_api_interfaces, init_digital_employees
from app.models.user import UserRepository

# 导入控制器
from app.controllers.auth import LoginHandler, LogoutHandler, UserLoginHandler, RegisterHandler
from app.controllers.home import AdminHandler, IndexHandler, WelcomeHandler
from app.controllers.user import UserListHandler, UserApiHandler, UserInfoHandler
from app.controllers.model import ModelListHandler, ModelApiHandler, ModelTokenStatsHandler, ModelChatHandler, ModelChatApiHandler, ModelOptionsHandler
from app.controllers.role import RoleListHandler, RoleApiHandler
from app.controllers.permission import PermissionListHandler, PermissionApiHandler
from app.controllers.function import FunctionListHandler, ModuleListHandler, FunctionApiHandler, ModuleApiHandler
from app.controllers.scout import ScoutListHandler, ScoutApiHandler, ScoutCollectHandler
from app.controllers.employee import EmployeeListHandler, EmployeeApiHandler, EmployeeChatHandler, EmployeeChatApiHandler, EmployeeListApiHandler
from app.controllers.interface import InterfaceListHandler, InterfaceApiHandler
from app.controllers.warehouse import WarehouseListHandler, WarehouseApiHandler, WarehouseDetailHandler, WarehouseStatsApiHandler
from app.controllers.deep_collect import DeepCollectListHandler, DeepCollectApiHandler, DeepCollectStatsApiHandler
from app.controllers.chat import ChatHandler, ChatApiHandler, ChatSessionListHandler
from app.controllers.datav import DataVListHandler, DataVScreenHandler, DataVApiHandler, DataVStatsApiHandler, DataVLocationApiHandler, DataVCacheClearHandler
from app.controllers.sentiment import SentimentListHandler, SentimentApiHandler, SentimentStatsApiHandler, SentimentAnalyzeHandler, SentimentDetailHandler
from wechat_chat.backend.chat_routes import get_chat_routes

def make_app():
    routes = [
            # 首页
            (r"/", IndexHandler),
            
            # 认证路由
            (r"/auth/login", LoginHandler),
            (r"/auth/user/login", UserLoginHandler),
            (r"/auth/register", RegisterHandler),
            (r"/auth/logout", LogoutHandler),
            
            # 后台主页
            (r"/admin", AdminHandler),
            (r"/admin/welcome", WelcomeHandler),
            
            # 用户管理路由
            (r"/admin/users", UserListHandler),
            (r"/api/users", UserApiHandler),
            (r"/api/user/info", UserInfoHandler),
            
            # 角色管理路由
            (r"/admin/roles", RoleListHandler),
            (r"/api/roles", RoleApiHandler),
            
            # 权限管理路由
            (r"/admin/permissions", PermissionListHandler),
            (r"/api/permissions", PermissionApiHandler),
            
            # 功能管理路由
            (r"/admin/functions", FunctionListHandler),
            (r"/admin/modules", ModuleListHandler),
            (r"/api/functions", FunctionApiHandler),
            (r"/api/modules", ModuleApiHandler),
            
            # 模型引擎路由
            (r"/admin/models", ModelListHandler),
            (r"/api/models", ModelApiHandler),
            (r"/api/models/token-stats", ModelTokenStatsHandler),
            (r"/api/models/options", ModelOptionsHandler),
            (r"/admin/models/chat", ModelChatHandler),
            (r"/api/models/chat", ModelChatApiHandler),
            
            # 瞭望管理路由
            (r"/admin/scout", ScoutListHandler),
            (r"/api/scout", ScoutApiHandler),
            (r"/admin/scout/collect", ScoutCollectHandler),
            
            # 数字员工路由
            (r"/admin/employees", EmployeeListHandler),
            (r"/admin/employees/chat", EmployeeChatHandler),
            (r"/api/employees", EmployeeApiHandler),
            (r"/api/employees/chat", EmployeeChatApiHandler),
            (r"/api/employees/list", EmployeeListApiHandler),
            
            # 接口管理路由
            (r"/admin/interfaces", InterfaceListHandler),
            (r"/api/interfaces", InterfaceApiHandler),
            
            # 数据仓库路由
            (r"/admin/warehouse", WarehouseListHandler),
            (r"/admin/warehouse/detail", WarehouseDetailHandler),
            (r"/api/warehouse", WarehouseApiHandler),
            (r"/api/warehouse/stats", WarehouseStatsApiHandler),

            # 数智大屏路由
            (r"/admin/datav", DataVListHandler),
            (r"/screen/datav", DataVScreenHandler),
            (r"/api/datav", DataVApiHandler),
            (r"/api/datav/stats", DataVStatsApiHandler),
            (r"/api/datav/location", DataVLocationApiHandler),
            (r"/api/datav/cache", DataVCacheClearHandler),

            # 智能舆情路由
            (r"/admin/sentiment", SentimentListHandler),
            (r"/api/sentiment", SentimentApiHandler),
            (r"/api/sentiment/stats", SentimentStatsApiHandler),
            (r"/api/sentiment/analyze", SentimentAnalyzeHandler),
            (r"/api/sentiment/detail/(\d+)", SentimentDetailHandler),

            # AI深度采集路由
            (r"/admin/deep-collect", DeepCollectListHandler),
            (r"/api/deep-collect", DeepCollectApiHandler),

            # 用户侧聊天路由
            (r"/chat", ChatHandler),
            (r"/api/chat", ChatApiHandler),
            (r"/api/chat/sessions", ChatSessionListHandler),
        ]
    
    # 整合子系统路由
    routes.extend(get_chat_routes())
    
    return tornado.web.Application(
        routes,
        template_path=os.path.join(os.path.dirname(__file__), "app", "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "app", "static"),
        cookie_secret="cnAgentOS-2026-secret-key-change-in-production",
        debug=True,
        xsrf_cookies=True,
        login_url="/auth/login",
    )

def init_admin_user():
    """初始化默认管理员用户"""
    if not UserRepository.get_user_by_username("admin"):
        UserRepository.create_user("admin", "admin888", "admin")
        print("默认管理员用户创建成功: admin/admin888")
    else:
        # 如果admin用户已存在但角色不是admin，更新角色
        user = UserRepository.get_user_by_username("admin")
        if user and user["role"] != "admin":
            UserRepository.update_user(user["id"], role="admin")
            print("已更新admin用户角色为超级管理员")

if __name__ == "__main__":
    init_db()
    init_admin_user()
    init_scout_sources()
    init_api_interfaces()
    init_digital_employees()
    
    app = make_app()
    server = HTTPServer(app)
    server.bind(10086)
    server.start()
    print("====== Server 启动成功 ====== 端口：10086 =======", flush=True)
    tornado.ioloop.IOLoop.current().start()
