import tornado.web
import tornado.gen
import json
import re
import sqlite3
from datetime import datetime

from app.controllers.base import BaseHandler
from app.models.user import UserRepository
from app.models.model_service import ModelServiceRepository
from app.models.chat import ChatSessionRepository, ChatMessageRepository
from app.models.digital_employee import DigitalEmployeeRepository
from app.models.api_interface import ApiInterfaceRepository
from app.models.warehouse import ScoutRecordRepository, ScoutDetailRepository
from app.models.db import get_connection, DB_PATH

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ChatHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/auth/user/login")
            return
        
        user = UserRepository.get_user_by_username(self.current_user)
        if not user:
            self.redirect("/auth/user/login")
            return
        
        xsrf_token = self.xsrf_token.decode('utf-8')
        models = ModelServiceRepository.get_all()
        default_model = ModelServiceRepository.get_default()
        sessions = ChatSessionRepository.get_by_user(user["id"])
        employees = DigitalEmployeeRepository.get_all()
        
        session_id = self.get_argument("session_id", "")
        current_session = None
        messages = []
        if session_id:
            current_session = ChatSessionRepository.get_by_id(int(session_id))
            if current_session and current_session["user_id"] == user["id"]:
                messages = ChatMessageRepository.get_by_session(int(session_id))
        
        self.render("chat.html", 
                    current_user=self.current_user, 
                    xsrf_token=xsrf_token,
                    models=models,
                    default_model=default_model,
                    sessions=sessions,
                    employees=employees,
                    current_session=current_session,
                    messages=messages)

class ChatApiHandler(BaseHandler):
    async def post(self):
        if not self.current_user:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "未登录"}))
            return
        
        user = UserRepository.get_user_by_username(self.current_user)
        if not user:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "用户不存在"}))
            return
        
        action = self.get_body_argument("action", "chat")
        
        if action == "create_session":
            await self._create_session(user)
        elif action == "delete_session":
            await self._delete_session(user)
        elif action == "get_messages":
            await self._get_messages(user)
        elif action == "chat":
            await self._chat(user)
        elif action == "stream":
            await self._stream_chat(user)
        else:
            self.write(json.dumps({"code": 1, "msg": "未知操作"}))
    
    async def _create_session(self, user):
        title = self.get_body_argument("title", "新对话")
        model_id = self.get_body_argument("model_id", "")
        employee_id = self.get_body_argument("employee_id", "")
        
        model_id = int(model_id) if model_id else None
        employee_id = int(employee_id) if employee_id else None
        
        session_id = ChatSessionRepository.create(
            user_id=user["id"],
            title=title,
            model_id=model_id,
            employee_id=employee_id
        )
        
        self.write(json.dumps({
            "code": 0,
            "msg": "创建成功",
            "data": {
                "session_id": session_id,
                "title": title
            }
        }))
    
    async def _delete_session(self, user):
        session_id = self.get_body_argument("session_id", "")
        if not session_id:
            self.write(json.dumps({"code": 1, "msg": "会话ID不能为空"}))
            return
        
        session = ChatSessionRepository.get_by_id(int(session_id))
        if not session or session["user_id"] != user["id"]:
            self.write(json.dumps({"code": 1, "msg": "会话不存在或无权限"}))
            return
        
        ChatSessionRepository.delete(int(session_id))
        self.write(json.dumps({"code": 0, "msg": "删除成功"}))
    
    async def _get_messages(self, user):
        session_id = self.get_body_argument("session_id", "")
        if not session_id:
            self.write(json.dumps({"code": 1, "msg": "会话ID不能为空"}))
            return
        
        session = ChatSessionRepository.get_by_id(int(session_id))
        if not session or session["user_id"] != user["id"]:
            self.write(json.dumps({"code": 1, "msg": "会话不存在或无权限"}))
            return
        
        messages = ChatMessageRepository.get_by_session(int(session_id))
        self.write(json.dumps({
            "code": 0,
            "data": messages
        }))
    
    async def _chat(self, user):
        session_id = self.get_body_argument("session_id", "")
        message = self.get_body_argument("message", "")
        model_id = self.get_body_argument("model_id", "")
        
        if not message:
            self.write(json.dumps({"code": 1, "msg": "消息不能为空"}))
            return
        
        if not session_id:
            title = message[:30] + ("..." if len(message) > 30 else "")
            model_id_int = int(model_id) if model_id else None
            session_id = ChatSessionRepository.create(
                user_id=user["id"],
                title=title,
                model_id=model_id_int
            )
        
        session = ChatSessionRepository.get_by_id(int(session_id))
        if not session or session["user_id"] != user["id"]:
            self.write(json.dumps({"code": 1, "msg": "会话不存在或无权限"}))
            return
        
        ChatMessageRepository.create(
            session_id=int(session_id),
            role="user",
            content=message
        )
        
        employee_match = re.match(r'^@(\S+)\s*(.*)', message)
        if employee_match:
            employee_alias = employee_match.group(1)
            user_message = employee_match.group(2).strip()
            response = await self._chat_with_employee(employee_alias, user_message, session)
        else:
            intent = await self._detect_intent(message)
            if intent == "database":
                response = await self._query_database(message, session)
            else:
                response = await self._chat_with_model(message, session)
        
        ChatMessageRepository.create(
            session_id=int(session_id),
            role="assistant",
            content=response
        )
        
        ChatSessionRepository.update(int(session_id), title=message[:30])
        
        self.write(json.dumps({
            "code": 0,
            "data": {
                "session_id": session_id,
                "response": response
            }
        }))
    
    async def _stream_chat(self, user):
        session_id = self.get_body_argument("session_id", "")
        message = self.get_body_argument("message", "")
        model_id = self.get_body_argument("model_id", "")
        
        if not message:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "消息不能为空"}))
            return
        
        if not session_id:
            title = message[:30] + ("..." if len(message) > 30 else "")
            model_id_int = int(model_id) if model_id else None
            session_id = ChatSessionRepository.create(
                user_id=user["id"],
                title=title,
                model_id=model_id_int
            )
        
        session = ChatSessionRepository.get_by_id(int(session_id))
        if not session or session["user_id"] != user["id"]:
            self.set_status(403)
            self.write(json.dumps({"code": 1, "msg": "会话不存在或无权限"}))
            return
        
        ChatMessageRepository.create(
            session_id=int(session_id),
            role="user",
            content=message
        )
        
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        
        employee_match = re.match(r'^@(\S+)\s*(.*)', message)
        if employee_match:
            employee_alias = employee_match.group(1)
            user_message = employee_match.group(2).strip()
            await self._stream_employee_chat(employee_alias, user_message, session, int(session_id))
        else:
            intent = await self._detect_intent(message)
            if intent == "database":
                response = await self._query_database(message, session)
                self._write_sse("data: " + json.dumps({"content": response}) + "\n\n")
                self._write_sse("data: [DONE]\n\n")
                ChatMessageRepository.create(
                    session_id=int(session_id),
                    role="assistant",
                    content=response
                )
            else:
                await self._stream_model_chat(message, session, int(session_id))
        
        ChatSessionRepository.update(int(session_id), title=message[:30])
    
    def _write_sse(self, data):
        self.write(data)
        self.flush()
    
    async def _detect_intent(self, message):
        keywords = ["数据", "记录", "采集", "最新", "多少条", "列表", "查询", "统计", "分析", "仓库"]
        if any(kw in message for kw in keywords):
            return "database"
        return "chat"
    
    async def _query_database(self, message, session):
        if not OPENAI_AVAILABLE:
            return "AI服务暂不可用"
        
        default_model = ModelServiceRepository.get_default()
        if not default_model:
            return "未配置默认模型"
        
        try:
            schema_info = self._get_database_schema()
            
            prompt = f"""你是一个SQL专家。根据用户的问题，生成SQLite查询语句。

数据库表结构：
{schema_info}

用户问题：{message}

请只返回SQL查询语句，不要有其他内容。如果无法生成SQL，请返回"无法生成SQL查询"。

注意：
1. 使用SQLite语法
2. 表名和字段名要准确
3. 对于模糊查询使用LIKE
4. 对于时间查询使用datetime函数"""

            client = OpenAI(
                api_key=default_model["api_key"],
                base_url=default_model["base_url"]
            )
            
            response = client.chat.completions.create(
                model=default_model["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            sql = response.choices[0].message.content.strip()
            sql = re.sub(r'^```sql\s*', '', sql)
            sql = re.sub(r'\s*```$', '', sql)
            sql = sql.strip()
            
            if sql.startswith("无法生成"):
                return "抱歉，我无法理解您的问题，请尝试更具体的描述。"
            
            try:
                with get_connection() as conn:
                    cursor = conn.execute(sql)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    if not rows:
                        return "查询结果为空，没有找到相关数据。"
                    
                    result_text = f"查询到 {len(rows)} 条记录：\n\n"
                    for i, row in enumerate(rows[:10], 1):
                        result_text += f"{i}. "
                        for j, col in enumerate(columns):
                            val = row[j]
                            if val:
                                result_text += f"{col}: {val} | "
                        result_text += "\n"
                    
                    if len(rows) > 10:
                        result_text += f"\n... 还有 {len(rows) - 10} 条记录"
                    
                    return result_text
                    
            except sqlite3.Error as e:
                return f"SQL执行错误：{str(e)}"
                
        except Exception as e:
            return f"查询失败：{str(e)}"
    
    def _get_database_schema(self):
        return """
表 scout_record（采集记录表）：
- id: 记录ID
- source_id: 数据源ID
- source_name: 数据源名称
- keyword: 关键字
- url: 原始URL
- title: 标题
- summary: 摘要
- status: 状态
- ai_analyzed: 是否已分析（0/1）
- collect_time: 采集时间

表 scout_detail（采集明细表）：
- id: 明细ID
- record_id: 关联记录ID
- title: 标题
- content: 内容
- author: 作者
- publish_time: 发布时间
- ai_summary: AI摘要
- ai_keywords: AI关键词
- ai_sentiment: AI情感分析

表 digital_employee（数字员工表）：
- id: 员工ID
- name: 名称
- alias: 别名
- category: 类别（AI/普通）
- description: 描述
"""
    
    async def _chat_with_model(self, message, session):
        if not OPENAI_AVAILABLE:
            return "AI服务暂不可用"
        
        model_id = session.get("model_id")
        if model_id:
            model = ModelServiceRepository.get_by_id(model_id)
        else:
            model = ModelServiceRepository.get_default()
        
        if not model:
            return "未配置模型服务"
        
        try:
            messages = ChatMessageRepository.get_recent_messages(session["id"], 10)
            chat_messages = []
            for msg in messages:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            chat_messages.append({"role": "user", "content": message})
            
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"]
            )
            
            response = client.chat.completions.create(
                model=model["model"],
                messages=chat_messages,
                max_tokens=model["max_tokens"],
                temperature=model["temperature"]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"对话失败：{str(e)}"
    
    async def _stream_model_chat(self, message, session, session_id):
        if not OPENAI_AVAILABLE:
            self._write_sse("data: " + json.dumps({"content": "AI服务暂不可用"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            return
        
        model_id = session.get("model_id")
        if model_id:
            model = ModelServiceRepository.get_by_id(model_id)
        else:
            model = ModelServiceRepository.get_default()
        
        if not model:
            self._write_sse("data: " + json.dumps({"content": "未配置模型服务"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            return
        
        try:
            messages = ChatMessageRepository.get_recent_messages(session_id, 10)
            chat_messages = []
            for msg in messages[:-1] if messages else []:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            chat_messages.append({"role": "user", "content": message})
            
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"]
            )
            
            full_response = ""
            stream = client.chat.completions.create(
                model=model["model"],
                messages=chat_messages,
                max_tokens=model["max_tokens"],
                temperature=model["temperature"],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self._write_sse("data: " + json.dumps({"content": content}) + "\n\n")
            
            self._write_sse("data: [DONE]\n\n")
            
            ChatMessageRepository.create(
                session_id=session_id,
                role="assistant",
                content=full_response
            )
            
        except Exception as e:
            self._write_sse("data: " + json.dumps({"content": f"对话失败：{str(e)}"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
    
    async def _chat_with_employee(self, employee_alias, message, session):
        employee = DigitalEmployeeRepository.get_by_alias(employee_alias)
        if not employee:
            return f"未找到数字员工 @{employee_alias}"
        
        if employee["category"] == "AI":
            return await self._chat_with_ai_employee(employee, message, session)
        else:
            return await self._chat_with_api_employee(employee, message)
    
    async def _chat_with_ai_employee(self, employee, message, session):
        if not OPENAI_AVAILABLE:
            return "AI服务暂不可用"
        
        model_id = employee.get("model_id")
        if model_id:
            model = ModelServiceRepository.get_by_id(model_id)
        else:
            model = ModelServiceRepository.get_default()
        
        if not model:
            return "未配置模型服务"
        
        try:
            system_prompt = employee.get("prompt", f"你是{employee['name']}，一个智能助手。")
            
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"]
            )
            
            response = client.chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=model["max_tokens"],
                temperature=model["temperature"]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"对话失败：{str(e)}"
    
    async def _chat_with_api_employee(self, employee, message):
        api_id = employee.get("api_interface_id")
        if not api_id:
            return "该员工未配置API接口"
        
        api_interface = ApiInterfaceRepository.get_by_id(api_id)
        if not api_interface:
            return "API接口不存在"
        
        try:
            import urllib.request
            import urllib.parse
            
            url = api_interface["url"]
            if employee["alias"] == "天气" and message:
                url = f"{url}?city={urllib.parse.quote(message)}"
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                result = response.read().decode('utf-8')
                data = json.loads(result)
                
                if employee["alias"] == "天气":
                    return self._format_weather_response(data)
                elif employee["alias"] == "音乐":
                    return self._format_music_response(data)
                else:
                    return json.dumps(data, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            return f"API调用失败：{str(e)}"
    
    async def _stream_employee_chat(self, employee_alias, message, session, session_id):
        employee = DigitalEmployeeRepository.get_by_alias(employee_alias)
        if not employee:
            self._write_sse("data: " + json.dumps({"content": f"未找到数字员工 @{employee_alias}"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            return
        
        if employee["category"] == "AI":
            await self._stream_ai_employee_chat(employee, message, session, session_id)
        else:
            response = await self._chat_with_api_employee(employee, message)
            self._write_sse("data: " + json.dumps({"content": response}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            ChatMessageRepository.create(
                session_id=session_id,
                role="assistant",
                content=response
            )
    
    async def _stream_ai_employee_chat(self, employee, message, session, session_id):
        if not OPENAI_AVAILABLE:
            self._write_sse("data: " + json.dumps({"content": "AI服务暂不可用"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            return
        
        model_id = employee.get("model_id")
        if model_id:
            model = ModelServiceRepository.get_by_id(model_id)
        else:
            model = ModelServiceRepository.get_default_model()
        
        if not model:
            self._write_sse("data: " + json.dumps({"content": "未配置模型服务"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
            return
        
        try:
            system_prompt = employee.get("prompt", f"你是{employee['name']}，一个智能助手。")
            
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"]
            )
            
            full_response = ""
            stream = client.chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=model["max_tokens"],
                temperature=model["temperature"],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self._write_sse("data: " + json.dumps({"content": content}) + "\n\n")
            
            self._write_sse("data: [DONE]\n\n")
            
            ChatMessageRepository.create(
                session_id=session_id,
                role="assistant",
                content=full_response
            )
            
        except Exception as e:
            self._write_sse("data: " + json.dumps({"content": f"对话失败：{str(e)}"}) + "\n\n")
            self._write_sse("data: [DONE]\n\n")
    
    def _format_weather_response(self, data):
        if not data or data.get("code") != 200:
            return "天气查询失败，请稍后重试"
        
        try:
            result = data.get("result", {})
            city = result.get("city", "未知城市")
            weather = result.get("weather", "未知")
            temp = result.get("temp", "未知")
            tempn = result.get("tempn", "未知")
            wind = result.get("wind", "未知")
            wd = result.get("wd", "未知")
            
            return f"🌍 {city} 天气\n\n🌡️ 温度：{tempn}°C ~ {temp}°C\n🌤️ 天气：{weather}\n💨 风向：{wd} {wind}"
        except:
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_music_response(self, data):
        if not data:
            return "音乐推荐失败，请稍后重试"
        
        try:
            if data.get("code") == 200:
                song = data.get("data", {})
                name = song.get("name", "未知歌曲")
                artist = song.get("artist", "未知歌手")
                url = song.get("url", "")
                return f"🎵 推荐歌曲\n\n🎶 歌曲：{name}\n👤 歌手：{artist}\n🔗 链接：{url}"
            else:
                return json.dumps(data, ensure_ascii=False, indent=2)
        except:
            return json.dumps(data, ensure_ascii=False, indent=2)

class ChatSessionListHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "未登录"}))
            return
        
        user = UserRepository.get_user_by_username(self.current_user)
        if not user:
            self.set_status(401)
            self.write(json.dumps({"code": 1, "msg": "用户不存在"}))
            return
        
        sessions = ChatSessionRepository.get_by_user(user["id"])
        self.write(json.dumps({
            "code": 0,
            "data": sessions
        }))
