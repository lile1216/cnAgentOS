import json
import tornado.web
import requests
from urllib.parse import urlparse

from app.controllers.base import BaseHandler
from app.models.scout_source import ScoutSourceRepository

class ScoutListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        # Layui 模板变量，用于前端模板渲染
        layui_status_template = "{{d.enabled == 1 ? 'enabled' : 'disabled'}}"
        layui_status_text_template = "{{d.enabled == 1 ? '启用' : '禁用'}}"
        layui_toggle_template = "{{d.enabled == 1 ? '禁用' : '启用'}}"
        self.render("scout_list.html", 
                    current_user=self.current_user, 
                    xsrf_token=xsrf_token,
                    layui_status_template=layui_status_template,
                    layui_status_text_template=layui_status_text_template,
                    layui_toggle_template=layui_toggle_template)

class ScoutApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page = 1
            page_size = 20
        
        sources = ScoutSourceRepository.get_all(page, page_size)
        total = ScoutSourceRepository.get_total_count()
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": sources
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_source()
        elif action == "edit":
            self._edit_source()
        elif action == "delete":
            self._delete_source()
        elif action == "batchDelete":
            self._batch_delete()
        elif action == "toggle":
            self._toggle_status()
        elif action == "collect":
            self._collect_data()
        elif action == "batchCollect":
            self._batch_collect()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_source(self):
        name = self.get_body_argument("name", "").strip()
        url_pattern = self.get_body_argument("url_pattern", "").strip()
        request_method = self.get_body_argument("request_method", "GET").strip().upper()
        headers = self.get_body_argument("headers", "")
        
        if not name or not url_pattern:
            self.write(json.dumps({"code": 1, "msg": "名称和URL模式不能为空"}))
            return
        
        if request_method not in ["GET", "POST"]:
            self.write(json.dumps({"code": 1, "msg": "请求方法只能是GET或POST"}))
            return
        
        if not self._validate_url(url_pattern):
            self.write(json.dumps({"code": 1, "msg": "无效的URL格式"}))
            return
        
        if ScoutSourceRepository.create(name, url_pattern, request_method, headers):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "名称已存在"}))

    def _edit_source(self):
        id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        url_pattern = self.get_body_argument("url_pattern", "").strip()
        request_method = self.get_body_argument("request_method", "").strip().upper()
        headers = self.get_body_argument("headers", "")
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
        if url_pattern:
            if not self._validate_url(url_pattern):
                self.write(json.dumps({"code": 1, "msg": "无效的URL格式"}))
                return
            update_params["url_pattern"] = url_pattern
        if request_method:
            if request_method not in ["GET", "POST"]:
                self.write(json.dumps({"code": 1, "msg": "请求方法只能是GET或POST"}))
                return
            update_params["request_method"] = request_method
        if headers is not None:
            update_params["headers"] = headers
        if enabled != "":
            update_params["enabled"] = enabled == "true"
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if ScoutSourceRepository.update(id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败，名称可能已存在"}))

    def _delete_source(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ScoutSourceRepository.delete(id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete(self):
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的数据源"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        deleted_count = ScoutSourceRepository.batch_delete(ids)
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
        
        if ScoutSourceRepository.toggle_status(id):
            self.write(json.dumps({"code": 0, "msg": "状态切换成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "状态切换失败"}))

    def _collect_data(self):
        id = self.get_body_argument("id", "")
        keywords = self.get_body_argument("keywords", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "数据源ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的数据源ID"}))
            return
        
        source = ScoutSourceRepository.get_by_id(id)
        if not source:
            self.write(json.dumps({"code": 1, "msg": "数据源不存在"}))
            return
        
        if not source["enabled"]:
            self.write(json.dumps({"code": 1, "msg": "数据源已禁用"}))
            return
        
        try:
            url = source["url_pattern"]
            if "{关键字}" in url:
                if not keywords:
                    self.write(json.dumps({"code": 1, "msg": "URL包含关键字占位符，请提供关键字"}))
                    return
                url = url.replace("{关键字}", keywords)
            
            headers = ScoutSourceRepository.parse_headers(source["headers"])
            
            response = requests.request(
                method=source["request_method"],
                url=url,
                headers=headers,
                timeout=30
            )
            
            self.write(json.dumps({
                "code": 0,
                "msg": "采集成功",
                "data": {
                    "url": url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text[:5000] if len(response.text) > 5000 else response.text,
                    "content_length": len(response.text)
                }
            }))
        
        except Exception as e:
            self.write(json.dumps({
                "code": 1,
                "msg": f"采集失败: {str(e)}"
            }))

    def _batch_collect(self):
        ids_str = self.get_body_argument("ids", "")
        keywords = self.get_body_argument("keywords", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要采集的数据源"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        results = []
        success_count = 0
        fail_count = 0
        
        for id in ids:
            source = ScoutSourceRepository.get_by_id(id)
            if not source or not source["enabled"]:
                results.append({
                    "id": id,
                    "name": source["name"] if source else "未知",
                    "success": False,
                    "msg": "数据源不存在或已禁用"
                })
                fail_count += 1
                continue
            
            try:
                url = source["url_pattern"]
                if "{关键字}" in url:
                    if not keywords:
                        results.append({
                            "id": id,
                            "name": source["name"],
                            "success": False,
                            "msg": "需要提供关键字"
                        })
                        fail_count += 1
                        continue
                    url = url.replace("{关键字}", keywords)
                
                headers = ScoutSourceRepository.parse_headers(source["headers"])
                
                response = requests.request(
                    method=source["request_method"],
                    url=url,
                    headers=headers,
                    timeout=30
                )
                
                results.append({
                    "id": id,
                    "name": source["name"],
                    "success": True,
                    "status_code": response.status_code,
                    "content_length": len(response.text)
                })
                success_count += 1
            
            except Exception as e:
                results.append({
                    "id": id,
                    "name": source["name"],
                    "success": False,
                    "msg": str(e)
                })
                fail_count += 1
        
        self.write(json.dumps({
            "code": 0,
            "msg": f"批量采集完成，成功 {success_count} 个，失败 {fail_count} 个",
            "data": results,
            "success_count": success_count,
            "fail_count": fail_count
        }))

    def _validate_url(self, url):
        """验证URL格式是否合法"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

class ScoutCollectHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", "")
        source_info = None
        if id:
            try:
                source_info = ScoutSourceRepository.get_by_id(int(id))
            except ValueError:
                pass
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("scout_collect.html", current_user=self.current_user, source_info=source_info, xsrf_token=xsrf_token)
