import json
import tornado.web
import tornado.gen
import tornado.escape

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from app.controllers.base import BaseHandler
from app.models.model_service import ModelServiceRepository

class ModelListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("model_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class ModelApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 6))
        except ValueError:
            page = 1
            page_size = 6
        
        models = ModelServiceRepository.get_all(page, page_size)
        total = ModelServiceRepository.get_total_count()
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": models
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_model()
        elif action == "edit":
            self._edit_model()
        elif action == "delete":
            self._delete_model()
        elif action == "setDefault":
            self._set_default()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_model(self):
        name = self.get_body_argument("name", "").strip()
        model = self.get_body_argument("model", "").strip()
        api_key = self.get_body_argument("api_key", "").strip()
        base_url = self.get_body_argument("base_url", "").strip()
        max_tokens = self.get_body_argument("max_tokens", "4096")
        temperature = self.get_body_argument("temperature", "0.7")
        is_default = self.get_body_argument("is_default", "false") == "true"
        
        if not name or not model or not api_key or not base_url:
            self.write(json.dumps({"code": 1, "msg": "名称、模型、API密钥和基础URL不能为空"}))
            return
        
        try:
            max_tokens = int(max_tokens)
            temperature = float(temperature)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "max_tokens必须为整数，temperature必须为浮点数"}))
            return
        
        if ModelServiceRepository.create(name, model, api_key, base_url, max_tokens, temperature, is_default):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "名称已存在"}))

    def _edit_model(self):
        id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        model = self.get_body_argument("model", "").strip()
        api_key = self.get_body_argument("api_key", "").strip()
        base_url = self.get_body_argument("base_url", "").strip()
        max_tokens = self.get_body_argument("max_tokens", "")
        temperature = self.get_body_argument("temperature", "")
        is_default = self.get_body_argument("is_default", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        update_params = {}
        if name:
            update_params["name"] = name
        if model:
            update_params["model"] = model
        if api_key:
            update_params["api_key"] = api_key
        if base_url:
            update_params["base_url"] = base_url
        if max_tokens:
            try:
                update_params["max_tokens"] = int(max_tokens)
            except ValueError:
                self.write(json.dumps({"code": 1, "msg": "max_tokens必须为整数"}))
                return
        if temperature:
            try:
                update_params["temperature"] = float(temperature)
            except ValueError:
                self.write(json.dumps({"code": 1, "msg": "temperature必须为浮点数"}))
                return
        if is_default != "":
            update_params["is_default"] = is_default == "true"
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if ModelServiceRepository.update(id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败，名称可能已存在"}))

    def _delete_model(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ModelServiceRepository.delete(id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _set_default(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ModelServiceRepository.update(id, is_default=True):
            self.write(json.dumps({"code": 0, "msg": "设置成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "设置失败"}))

class ModelTokenStatsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        stats = ModelServiceRepository.get_token_stats()
        self.write(json.dumps({"code": 0, "msg": "success", "data": stats}))

class ModelOptionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        models = ModelServiceRepository.get_all_options()
        self.write(json.dumps({"code": 0, "msg": "success", "data": models}))

class ModelChatHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        model_id = self.get_argument("model_id", "")
        model_info = None
        if model_id:
            try:
                model_info = ModelServiceRepository.get_by_id(int(model_id))
            except ValueError:
                pass
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("model_chat.html", current_user=self.current_user, model_info=model_info, xsrf_token=xsrf_token)

class ModelChatApiHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self):
        if not OPENAI_AVAILABLE:
            self.write(json.dumps({"code": 1, "msg": "openai模块未安装，请先安装: pip install openai"}))
            return
        
        model_id = self.get_body_argument("model_id", "")
        message = self.get_body_argument("message", "").strip()
        
        if not model_id or not message:
            self.write(json.dumps({"code": 1, "msg": "模型ID和消息不能为空"}))
            return
        
        try:
            model_id = int(model_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的模型ID"}))
            return
        
        model_info = ModelServiceRepository.get_by_id(model_id)
        if not model_info:
            self.write(json.dumps({"code": 1, "msg": "模型不存在"}))
            return
        
        stream = self.get_body_argument("stream", "false") == "true"
        
        if stream:
            yield self._stream_response(model_info, message)
        else:
            yield self._normal_response(model_info, message)

    @tornado.gen.coroutine
    def _stream_response(self, model_info, message):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        
        try:
            client = OpenAI(
                api_key=model_info["api_key"],
                base_url=model_info["base_url"]
            )
            
            response = client.chat.completions.create(
                model=model_info["model"],
                messages=[{"role": "user", "content": message}],
                max_tokens=model_info["max_tokens"],
                temperature=model_info["temperature"],
                stream=True
            )
            
            full_response = ""
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.write(f"data: {tornado.escape.json_encode({'content': content, 'done': False})}\n\n")
                    yield tornado.gen.maybe_future(self.flush())
            
            self.write(f"data: {tornado.escape.json_encode({'content': '', 'done': True})}\n\n")
            yield tornado.gen.maybe_future(self.flush())
            
            token_count = len(full_response) // 4
            ModelServiceRepository.update_token_usage(model_info["id"], token_count)
            
        except Exception as e:
            self.write(f"data: {tornado.escape.json_encode({'content': f'错误: {str(e)}', 'done': True})}\n\n")
            yield tornado.gen.maybe_future(self.flush())

    @tornado.gen.coroutine
    def _normal_response(self, model_info, message):
        try:
            client = OpenAI(
                api_key=model_info["api_key"],
                base_url=model_info["base_url"]
            )
            
            response = client.chat.completions.create(
                model=model_info["model"],
                messages=[{"role": "user", "content": message}],
                max_tokens=model_info["max_tokens"],
                temperature=model_info["temperature"]
            )
            
            content = response.choices[0].message.content
            token_count = response.usage.total_tokens if hasattr(response, 'usage') else len(content) // 4
            
            ModelServiceRepository.update_token_usage(model_info["id"], token_count)
            
            self.write(json.dumps({"code": 0, "msg": "success", "data": content}))
            
        except Exception as e:
            self.write(json.dumps({"code": 1, "msg": str(e)}))
