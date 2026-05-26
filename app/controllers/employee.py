import json
import tornado.web
import tornado.gen
import tornado.escape
import requests
from urllib.parse import quote

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from app.controllers.base import BaseHandler
from app.models.digital_employee import DigitalEmployeeRepository
from app.models.model_service import ModelServiceRepository
from app.models.api_interface import ApiInterfaceRepository

class EmployeeListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("employee_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class EmployeeChatHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        alias = self.get_argument("alias", "")
        employee = None
        if alias:
            employee = DigitalEmployeeRepository.get_by_alias(alias)
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("employee_chat.html", current_user=self.current_user, employee=employee, xsrf_token=xsrf_token)

class EmployeeApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page = 1
            page_size = 20
        
        try:
            employees = DigitalEmployeeRepository.get_all(page, page_size)
            total = DigitalEmployeeRepository.get_total_count()
            
            for emp in employees:
                if emp.get("model_id"):
                    model = ModelServiceRepository.get_by_id(emp["model_id"])
                    emp["model_name"] = model["name"] if model else None
                if emp.get("api_interface_id"):
                    api = ApiInterfaceRepository.get_by_id(emp["api_interface_id"])
                    emp["api_name"] = api["name"] if api else None
            
            self.write(json.dumps({
                "code": 0,
                "msg": "success",
                "count": total,
                "data": employees
            }))
        except Exception as e:
            self.write(json.dumps({
                "code": 1,
                "msg": f"获取数据失败: {str(e)}",
                "count": 0,
                "data": []
            }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_employee()
        elif action == "edit":
            self._edit_employee()
        elif action == "delete":
            self._delete_employee()
        elif action == "batchDelete":
            self._batch_delete()
        elif action == "toggle":
            self._toggle_status()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_employee(self):
        name = self.get_body_argument("name", "").strip()
        alias = self.get_body_argument("alias", "").strip()
        category = self.get_body_argument("category", "AI").strip()
        description = self.get_body_argument("description", "").strip()
        prompt = self.get_body_argument("prompt", "").strip() or None
        model_id = self.get_body_argument("model_id", "") or None
        api_interface_id = self.get_body_argument("api_interface_id", "") or None
        avatar = self.get_body_argument("avatar", "🤖").strip()
        welcome_msg = self.get_body_argument("welcome_msg", "").strip()
        enabled = self.get_body_argument("enabled", "true") == "true"
        
        if not name or not alias:
            self.write(json.dumps({"code": 1, "msg": "名称和别名不能为空"}))
            return
        
        if category not in ["AI", "普通"]:
            self.write(json.dumps({"code": 1, "msg": "类别只能是AI或普通"}))
            return
        
        if model_id:
            try:
                model_id = int(model_id)
            except ValueError:
                model_id = None
        
        if api_interface_id:
            try:
                api_interface_id = int(api_interface_id)
            except ValueError:
                api_interface_id = None
        
        if DigitalEmployeeRepository.create(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "别名已存在"}))

    def _edit_employee(self):
        id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        alias = self.get_body_argument("alias", "").strip()
        category = self.get_body_argument("category", "").strip()
        description = self.get_body_argument("description", "").strip()
        prompt = self.get_body_argument("prompt", "").strip()
        model_id = self.get_body_argument("model_id", "")
        api_interface_id = self.get_body_argument("api_interface_id", "")
        avatar = self.get_body_argument("avatar", "").strip()
        welcome_msg = self.get_body_argument("welcome_msg", "").strip()
        enabled = self.get_body_argument("enabled", "")
        
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
        if alias:
            update_params["alias"] = alias
        if category:
            if category not in ["AI", "普通"]:
                self.write(json.dumps({"code": 1, "msg": "类别只能是AI或普通"}))
                return
            update_params["category"] = category
        if description is not None:
            update_params["description"] = description
        if prompt is not None:
            update_params["prompt"] = prompt if prompt else None
        if model_id != "":
            update_params["model_id"] = int(model_id) if model_id else None
        if api_interface_id != "":
            update_params["api_interface_id"] = int(api_interface_id) if api_interface_id else None
        if avatar is not None:
            update_params["avatar"] = avatar
        if welcome_msg is not None:
            update_params["welcome_msg"] = welcome_msg
        if enabled != "":
            update_params["enabled"] = enabled == "true"
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if DigitalEmployeeRepository.update(id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败，别名可能已存在"}))

    def _delete_employee(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if DigitalEmployeeRepository.delete(id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete(self):
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的数字员工"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        deleted_count = DigitalEmployeeRepository.batch_delete(ids)
        self.write(json.dumps({
            "code": 0,
            "msg": f"成功删除 {deleted_count} 条记录"
        }))

    def _toggle_status(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if DigitalEmployeeRepository.toggle_status(id):
            self.write(json.dumps({"code": 0, "msg": "状态切换成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "状态切换失败"}))

class EmployeeChatApiHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self):
        alias = self.get_body_argument("alias", "").strip()
        message = self.get_body_argument("message", "").strip()
        
        if not alias or not message:
            self.write(json.dumps({"code": 1, "msg": "别名和消息不能为空"}))
            return
        
        employee = DigitalEmployeeRepository.get_by_alias(alias)
        if not employee:
            self.write(json.dumps({"code": 1, "msg": "数字员工不存在或已禁用"}))
            return
        
        if employee["category"] == "AI":
            yield self._handle_ai_employee(employee, message)
        else:
            yield self._handle_normal_employee(employee, message)

    @tornado.gen.coroutine
    def _handle_ai_employee(self, employee, message):
        if not OPENAI_AVAILABLE:
            self.write(json.dumps({"code": 1, "msg": "openai模块未安装，请先安装: pip install openai"}))
            return
        
        model_id = employee.get("model_id")
        if not model_id:
            default_model = ModelServiceRepository.get_default()
            if not default_model:
                self.write(json.dumps({"code": 1, "msg": "未配置默认模型，请先在模型管理中设置"}))
                return
            model_info = default_model
        else:
            model_info = ModelServiceRepository.get_by_id(model_id)
            if not model_info:
                self.write(json.dumps({"code": 1, "msg": "关联的模型不存在"}))
                return
        
        stream = self.get_body_argument("stream", "true") == "true"
        
        if stream:
            yield self._stream_ai_response(model_info, employee, message)
        else:
            yield self._normal_ai_response(model_info, employee, message)

    @tornado.gen.coroutine
    def _stream_ai_response(self, model_info, employee, message):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        
        try:
            client = OpenAI(
                api_key=model_info["api_key"],
                base_url=model_info["base_url"]
            )
            
            messages = []
            if employee.get("prompt"):
                messages.append({"role": "system", "content": employee["prompt"]})
            messages.append({"role": "user", "content": message})
            
            response = client.chat.completions.create(
                model=model_info["model"],
                messages=messages,
                max_tokens=model_info["max_tokens"],
                temperature=model_info["temperature"],
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    self.write(f"data: {tornado.escape.json_encode({'content': content, 'done': False})}\n\n")
                    yield tornado.gen.maybe_future(self.flush())
            
            self.write(f"data: {tornado.escape.json_encode({'content': '', 'done': True})}\n\n")
            yield tornado.gen.maybe_future(self.flush())
            
        except Exception as e:
            self.write(f"data: {tornado.escape.json_encode({'content': f'错误: {str(e)}', 'done': True})}\n\n")
            yield tornado.gen.maybe_future(self.flush())

    @tornado.gen.coroutine
    def _normal_ai_response(self, model_info, employee, message):
        try:
            client = OpenAI(
                api_key=model_info["api_key"],
                base_url=model_info["base_url"]
            )
            
            messages = []
            if employee.get("prompt"):
                messages.append({"role": "system", "content": employee["prompt"]})
            messages.append({"role": "user", "content": message})
            
            response = client.chat.completions.create(
                model=model_info["model"],
                messages=messages,
                max_tokens=model_info["max_tokens"],
                temperature=model_info["temperature"]
            )
            
            content = response.choices[0].message.content
            self.write(json.dumps({"code": 0, "msg": "success", "data": content}))
            
        except Exception as e:
            self.write(json.dumps({"code": 1, "msg": str(e)}))

    @tornado.gen.coroutine
    def _handle_normal_employee(self, employee, message):
        api_interface_id = employee.get("api_interface_id")
        if not api_interface_id:
            self.write(json.dumps({"code": 1, "msg": "该数字员工未关联API接口"}))
            return
        
        api_info = ApiInterfaceRepository.get_by_id(api_interface_id)
        if not api_info:
            self.write(json.dumps({"code": 1, "msg": "关联的API接口不存在"}))
            return
        
        try:
            url = api_info["url"]
            
            if "{city}" in url or "{城市}" in url:
                url = url.replace("{city}", quote(message)).replace("{城市}", quote(message))
            elif "{keyword}" in url or "{关键字}" in url:
                url = url.replace("{keyword}", quote(message)).replace("{关键字}", quote(message))
            
            response = requests.request(
                method=api_info["method"],
                url=url,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.write(json.dumps({
                        "code": 0,
                        "msg": "success",
                        "data": data,
                        "employee": {
                            "name": employee["name"],
                            "alias": employee["alias"],
                            "avatar": employee["avatar"]
                        }
                    }))
                except:
                    self.write(json.dumps({
                        "code": 0,
                        "msg": "success",
                        "data": response.text,
                        "employee": {
                            "name": employee["name"],
                            "alias": employee["alias"],
                            "avatar": employee["avatar"]
                        }
                    }))
            else:
                self.write(json.dumps({"code": 1, "msg": f"API请求失败，状态码: {response.status_code}"}))
        
        except Exception as e:
            self.write(json.dumps({"code": 1, "msg": f"请求失败: {str(e)}"}))

class EmployeeListApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        employees = DigitalEmployeeRepository.get_enabled_employees()
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "data": employees
        }))
