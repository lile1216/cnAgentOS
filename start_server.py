#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""优化后的启动脚本，减少初始化时间"""

import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
import os

# 只导入必要的模块，避免启动时加载过重
from app.models.db import init_db, init_scout_sources, init_api_interfaces, init_digital_employees
from app.models.user import UserRepository

# 延迟导入控制器，加快启动速度
def import_controllers():
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
    
    return [
        (r"/", IndexHandler),
        (r"/auth/login", LoginHandler),
        (r"/auth/user/login", UserLoginHandler),
        (r"/auth/register", RegisterHandler),
        (r"/auth/logout", LogoutHandler),
        (r"/admin", AdminHandler),
        (r"/admin/welcome", WelcomeHandler),
        (r"/admin/users", UserListHandler),
        (r"/api/users", UserApiHandler),
        (r"/api/user/info", UserInfoHandler),
        (r"/admin/roles", RoleListHandler),
        (r"/api/roles", RoleApiHandler),
        (r"/admin/permissions", PermissionListHandler),
        (r"/api/permissions", PermissionApiHandler),
        (r"/admin/functions", FunctionListHandler),
        (r"/admin/modules", ModuleListHandler),
        (r"/api/functions", FunctionApiHandler),
        (r"/api/modules", ModuleApiHandler),
        (r"/admin/models", ModelListHandler),
        (r"/api/models", ModelApiHandler),
        (r"/api/models/token-stats", ModelTokenStatsHandler),
        (r"/api/models/options", ModelOptionsHandler),
        (r"/admin/models/chat", ModelChatHandler),
        (r"/api/models/chat", ModelChatApiHandler),
        (r"/admin/scout", ScoutListHandler),
        (r"/api/scout", ScoutApiHandler),
        (r"/admin/scout/collect", ScoutCollectHandler),
        (r"/admin/employees", EmployeeListHandler),
        (r"/admin/employees/chat", EmployeeChatHandler),
        (r"/api/employees", EmployeeApiHandler),
        (r"/api/employees/chat", EmployeeChatApiHandler),
        (r"/api/employees/list", EmployeeListApiHandler),
        (r"/admin/interfaces", InterfaceListHandler),
        (r"/api/interfaces", InterfaceApiHandler),
        (r"/admin/warehouse", WarehouseListHandler),
        (r"/api/warehouse", WarehouseApiHandler),
        (r"/api/warehouse/detail", WarehouseDetailHandler),
        (r"/api/warehouse/stats", WarehouseStatsApiHandler),
        (r"/admin/deep-collect", DeepCollectListHandler),
        (r"/api/deep-collect", DeepCollectApiHandler),
        (r"/api/deep-collect/stats", DeepCollectStatsApiHandler),
        (r"/chat", ChatHandler),
        (r"/api/chat", ChatApiHandler),
        (r"/api/chat/sessions", ChatSessionListHandler),
        (r"/admin/datav", DataVListHandler),
        (r"/screen/datav", DataVScreenHandler),
        (r"/api/datav", DataVApiHandler),
        (r"/api/datav/stats", DataVStatsApiHandler),
        (r"/api/datav/location", DataVLocationApiHandler),
        (r"/api/datav/cache/clear", DataVCacheClearHandler),
        (r"/admin/sentiment", SentimentListHandler),
        (r"/api/sentiment", SentimentApiHandler),
        (r"/api/sentiment/stats", SentimentStatsApiHandler),
        (r"/api/sentiment/analyze", SentimentAnalyzeHandler),
        (r"/api/sentiment/detail", SentimentDetailHandler),
    ]

def make_app():
    routes = import_controllers()
    
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

if __name__ == "__main__":
    print("正在初始化数据库...", flush=True)
    init_db()
    init_admin_user()
    
    print("正在初始化数据源...", flush=True)
    init_scout_sources()
    init_api_interfaces()
    init_digital_employees()
    
    print("正在启动服务器...", flush=True)
    app = make_app()
    server = HTTPServer(app)
    server.bind(10086)
    server.start(1)  # 使用单进程，避免多进程问题
    print("====== Server 启动成功 ====== 端口：10086 =======", flush=True)
    tornado.ioloop.IOLoop.current().start()
