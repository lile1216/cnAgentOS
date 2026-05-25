# cnAgentOS 项目学习文档

## 一、项目概述

### 1.1 项目简介
cnAgentOS 是一个基于 Tornado Web 框架的 B/S 架构系统，采用 MVC 设计模式，目前已实现用户登录功能。

### 1.2 技术栈
| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端语言 | Python | 3.12 | 主要开发语言 |
| 数据库 | SQLite3 | - | 轻量级嵌入式数据库 |
| Web框架 | Tornado | 6.5.5 | 异步Web框架 |
| 前端基础 | HTML5 + CSS + JavaScript | - | 前端三件套 |
| UI框架 | Bootstrap | 5.3.8 | 响应式UI框架 |
| UI框架 | Layui | 2.13.6 | 国产模块化UI框架 |
| 图标库 | FontAwesome | 5.15.4 | 图标字体库 |

### 1.2.1 前端组件库本地化路径
| 组件 | 路径 | 状态 |
|------|------|------|
| Bootstrap 5.3.8 | `/app/static/dist/bootstrap-5.3.8-dist/` | 已部署 |
| FontAwesome 5.15.4 | `/app/static/dist/fontawesome-free-5.15.4-web/` | 已部署 |
| Layui 2.13.6 | `/app/static/dist/layui-v2.13.6/layui/` | 已部署 |

### 1.3 项目目录结构

```
cnAgentOS/
├── app/                          # 应用主目录
│   ├── __init__.py               # 应用包初始化（空）
│   │
│   ├── controllers/               # 控制器层（MVC-C）
│   │   ├── __init__.py           # 控制器包初始化（空）
│   │   ├── base.py               # 基类控制器
│   │   ├── auth.py               # 认证控制器（登录）
│   │   └── home.py               # 首页控制器（空）
│   │
│   ├── models/                   # 模型层（MVC-M）
│   │   ├── __init__.py           # 模型包初始化（空）
│   │   ├── db.py                 # 数据库连接与初始化
│   │   └── user.py               # 用户模型与仓库
│   │
│   ├── templates/                # 视图模板目录
│   │   ├── login.html            # 登录模板
│   │   └── register.html         # 注册模板
│   │
│   └── static/                   # 静态资源目录
│       ├── css/                  # CSS样式目录（空）
│       ├── js/                   # JavaScript目录（空）
│       └── dist/                 # 第三方组件库目录
│           ├── bootstrap-5.3.8-dist/     # Bootstrap 5.3.8
│           │   ├── css/          # Bootstrap CSS文件
│           │   └── js/           # Bootstrap JS文件
│           ├── fontawesome-free-5.15.4-web/  # FontAwesome 5.15.4
│           │   ├── css/          # FontAwesome CSS文件
│           │   ├── js/           # FontAwesome JS文件
│           │   └── webfonts/     # 字体文件
│           └── layui-v2.13.6/     # Layui 2.13.6
│               └── layui/          # Layui核心文件
│                   ├── css/        # Layui CSS文件
│                   ├── font/        # Layui字体文件
│                   └── layui.js    # Layui主JS文件
│
├── database/                     # 数据库目录
│   └── app.db                    # SQLite数据库文件
│
├── venv/                         # Python虚拟环境
│
├── app.py                        # 根目录入口文件（测试代码）
├── app.md                        # 项目原始规范文档
└── cnAgentOS.txt                 # 项目说明文档
```

---

## 二、架构设计

### 2.1 MVC架构

```
┌─────────────────────────────────────────────────────────┐
│                      View (Templates)                   │
│         login.html, register.html, admin.html           │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 渲染/响应
┌─────────────────────────────────────────────────────────┐
│                  Controller (Controllers)               │
│   BaseHandler → LoginHandler, HomeHandler, AuthHandler    │
│   职责: 处理请求、调用模型、返回视图                        │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 调用
┌─────────────────────────────────────────────────────────┐
│                     Model (Models)                      │
│   UserRepository, db.py                                  │
│   职责: 数据操作、业务逻辑、数据库交互                     │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 查询
┌─────────────────────────────────────────────────────────┐
│                   Database (SQLite3)                    │
│   database/app.db                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 B/S请求处理流程

```
Browser (客户端)
     │
     │ HTTP Request (GET /auth/login)
     ▼
Tornado Application (app.py)
     │
     ├── URL路由匹配 → LoginHandler
     │
     ├── GET: 渲染登录表单
     │
     └── POST: 接收表单数据 → 调用UserRepository验证
                          ├── 成功 → 设置Cookie → 重定向到首页
                          └── 失败 → 返回错误表单
```

### 2.3 安全机制

1. **XSRF Protection**: Tornado内置的跨站请求伪造防护
   - 通过 `xsrf_form_html()` 在表单中生成隐藏token
   - POST请求自动验证token有效性

2. **密码加密**: PBKDF2-SHA256
   - 算法: SHA256
   - 迭代次数: 100,000次
   - Salt长度: 16字节（随机生成）

3. **Session管理**: 基于Cookie的会话
   - 使用 `set_secure_cookie()` / `get_secure_cookie()`
   - `get_current_user()` 方法获取当前登录用户

---

## 三、核心代码分析

### 3.1 控制器层 (Controllers)

#### 3.1.1 BaseHandler (`app/controllers/base.py`)

**文件路径**: `f:\20260515cNy\day4\cnAgentOS\app\controllers\base.py`

```python
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("username")
        if not username:
            return None
        return username.decode('utf-8')
```

**功能说明**:
- 所有控制器的基类
- 继承自 `tornado.web.RequestHandler`
- 提供 `get_current_user()` 方法用于获取当前登录用户
- 从安全Cookie中读取username并解码为UTF-8字符串

**关键方法**:
| 方法 | 作用 |
|------|------|
| `get_current_user()` | 获取当前登录用户的用户名，未登录返回None |

#### 3.1.2 LoginHandler (`app/controllers/auth.py`)

**文件路径**: `f:\20260515cNy\day4\cnAgentOS\app\controllers\auth.py`

```python
import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository

class LoginHandler(BaseHandler):
    def get(self):
        self.write(f"""<h3>登录</h3>
            <form method="post" action="/auth/login">
            <input name="username">
            <input name="password">
            <button type="submit">登录</button>
            {self.xsrf_form_html()}
            </form>
            """)

    def post(self):
        username = (self.get_body_argument("username","") or "").strip()
        password = self.get_body_argument("password","")
        if not username or not password:
            self.set_status(400)
            return self.write(f"""<h3>登录</h3>
            用户名或密码不能为空或输入了无效数据
            <form method="post" action="/auth/login">
            <input name="username">
            <input name="password">
            <button type="submit">登录admin</button>
            {self.xsrf_form_html()}
            </form>
            """)
```

**功能说明**:
- 处理用户登录请求
- GET: 显示登录表单
- POST: 验证用户凭证（注：当前代码只做了非空验证，尚未调用UserRepository验证）

**路由配置**:
- 路由路径: `/auth/login`
- 请求方法: GET, POST

**待完善**:
- POST方法中需要调用 `UserRepository.verify_user()` 验证用户名密码
- 验证成功后需要调用 `self.set_secure_cookie("username", username)`
- 验证成功后需要重定向到首页

---

### 3.2 模型层 (Models)

#### 3.2.1 数据库模块 (`app/models/db.py`)

**文件路径**: `f:\20260515cNy\day4\cnAgentOS\app\models\db.py`

```python
import os
import sqlite3

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))

DB_PATH = os.path.join(_project_root(),"database","app.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user(
                id integer PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
            """
        )
```

**功能说明**:
- 提供数据库连接和初始化功能
- 数据库文件位于: `database/app.db`

**关键函数**:
| 函数 | 作用 |
|------|------|
| `_project_root()` | 获取项目根目录路径 |
| `get_connection()` | 获取SQLite数据库连接，设置Row工厂 |
| `init_db()` | 初始化user表（如果不存在） |

**数据库表结构**:
```sql
CREATE TABLE IF NOT EXISTS user(
    id integer PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    create_at TEXT NOT NULL DEFAULT(datetime('now'))
)
```

**字段说明**:
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID，自增 |
| username | TEXT | NOT NULL UNIQUE | 用户名，唯一 |
| password_hash | TEXT | NOT NULL | 密码哈希值 |
| salt | TEXT | NOT NULL | 盐值（16字节hex编码） |
| create_at | TEXT | NOT NULL DEFAULT(datetime('now')) | 创建时间 |

#### 3.2.2 用户模型 (`app/models/user.py`)

**文件路径**: `f:\20260515cNy\day4\cnAgentOS\app\models\user.py`

```python
import hashlib
import secrets
import sqlite3

from app.models.db import get_connection

# 密码加密方法
def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()

# 用户对象类
class UserRepository:
    # 创建用户方法
    @staticmethod
    def create_user(username: str, password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)

        try:
            with get_connection() as conn:
                conn.execute(
                    "insert into user(username,password_hash,salt) values(?,?,?)",
                    (username, password_hash, salt.hex())
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_user_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "select id,username,password_hash,salt from user where username = ?",
                (username,)
            ).fetchone()
        return row

    # 验证用户名和密码的方法
    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        row = UserRepository.get_user_by_username(username)
        if not row:
            return False

        salt = bytes.fromhex(row["salt"])
        return _hash_password(password, salt) == row["password_hash"]
```

**功能说明**:
- 用户数据访问对象（Repository模式）
- 提供用户创建、查询、验证功能
- 密码采用PBKDF2-SHA256算法加密

**关键方法**:
| 方法 | 作用 | 返回值 |
|------|------|--------|
| `create_user(username, password)` | 创建新用户 | bool: 成功返回True，用户名冲突返回False |
| `get_user_by_username(username)` | 根据用户名查询用户 | Row对象或None |
| `verify_user(username, password)` | 验证用户密码 | bool: 验证成功返回True |

**密码加密细节**:
- 算法: PBKDF2-HMAC-SHA256
- 迭代次数: 100,000
- Salt: 16字节随机值，hex编码存储
- 输出: 64字符hex字符串

---

### 3.3 视图层 (Templates)

当前模板文件均为空文件，待开发使用：

| 文件 | 用途 | 状态 |
|------|------|------|
| base.html | 基础模板 | 空 |
| indext.html | 首页模板 | 空 |
| login.html | 登录页模板 | 空 |
| register.html | 注册页模板 | 空 |

---

### 3.4 静态资源 (Static)

当前目录为空，待开发：

| 目录 | 用途 | 状态 |
|------|------|------|
| static/css/ | CSS样式文件 | 空 |
| static/js/ | JavaScript文件 | 空 |

---

## 四、已实现功能分析

### 4.1 登录功能（部分完成）

**当前状态**: 表单展示和基础验证已完成，完整验证流程待实现

**实现内容**:
1. ✓ 登录页面GET请求处理 - 返回登录表单HTML
2. ✓ XSRF令牌保护 - 通过 `xsrf_form_html()` 生成
3. ✓ 表单基础验证 - 非空检查
4. ✓ 错误信息回显 - 验证失败时显示错误

**待完善内容**:
1. 调用 `UserRepository.verify_user()` 验证用户名密码
2. 验证成功后设置安全Cookie: `self.set_secure_cookie("username", username)`
3. 验证成功后重定向到首页或其他页面
4. 数据库初始化调用 `init_db()`

---

## 五、根目录app.py说明

**文件路径**: `f:\20260515cNy\day4\cnAgentOS\app.py`

当前该文件为测试代码/占位代码，包含未完成的类和方法，不是实际的应用入口。

**实际应用入口尚未完善**，建议后续开发时创建统一的应用入口文件。

---

## 六、后续开发指南

### 6.1 待开发功能

根据项目定位（AI智能瞭望与智能问答系统），待开发功能包括：

1. **用户注册功能**
   - 创建 RegisterHandler
   - 调用 UserRepository.create_user()
   - 路由: /auth/register

2. **用户登出功能**
   - 清除安全Cookie
   - 路由: /auth/logout

3. **首页功能**
   - 完成 HomeHandler
   - 受保护的路由，需要登录
   - 路由: /home 或 /index

4. **AI智能瞭望功能**
   - 瞭望数据展示
   - 实时数据更新
   - 路由设计待定

5. **智能问答功能**
   - 问答界面
   - 与AI服务集成
   - 路由设计待定

### 6.2 开发建议

1. **模板开发**
   - 完善 base.html 作为基础模板（导航栏、页脚、样式引入）
   - 开发 login.html 和 register.html 替换内联HTML
   - 开发 index.html 作为登录后的首页

2. **静态资源**
   - 添加 CSS 样式文件
   - 添加 JavaScript 文件（可选AJAX交互）

3. **应用入口**
   - 完善 app.py 或新建入口文件
   - 配置 URL路由映射
   - 配置模板路径和静态文件路径
   - 配置Cookie_secret_key

4. **数据库初始化**
   - 在应用启动时调用 init_db()
   - 确保database目录存在

5. **安全增强**
   - 添加密码强度验证
   - 添加登录尝试次数限制
   - 添加用户会话管理

### 6.3 Tornado应用配置示例

```python
import tornado.web
from tornado.httpserver import HTTPServer
from app.models.db import init_db

def make_app():
    return tornado.web.Application(
        [
            # 路由配置
            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/auth/register", RegisterHandler),
            (r"/home", HomeHandler),
            (r"/", IndexHandler),
        ],
        template_path="app/templates",
        static_path="app/static",
        cookie_secret="your-secret-key-here",
        debug=True,
        xsrf_cookies=True,
    )

if __name__ == "__main__":
    init_db()  # 初始化数据库
    app = make_app()
    server = HTTPServer(app)
    server.bind(10086)
    server.start()
    print("====== Server 启动成功 ====== 端口：10086 =======")
    tornado.ioloop.IOLoop.current().start()
```

---

## 七、数据库初始化

首次部署时需要初始化数据库表。在应用启动时调用：

```python
from app.models.db import init_db
init_db()
```

---

## 八、注意事项

1. **不修改现有代码**: 本文档记录的学习内容，不涉及对现有代码的修改
2. **UTF-8编码**: 确保所有文件保存为UTF-8编码
3. **Python版本**: 项目使用Python 3.12
4. **依赖**: Tornado 6.5.5, SQLite3（Python内置）
5. **Cookie Secret**: 生产环境需要设置复杂的cookie_secret_key
