import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.api_interface import ApiInterfaceRepository

class InterfaceListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("interface_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class InterfaceApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page = 1
            page_size = 20
        
        interfaces = ApiInterfaceRepository.get_all(page, page_size)
        total = ApiInterfaceRepository.get_total_count()
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": interfaces
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_interface()
        elif action == "edit":
            self._edit_interface()
        elif action == "delete":
            self._delete_interface()
        elif action == "batchDelete":
            self._batch_delete()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_interface(self):
        name = self.get_body_argument("name", "").strip()
        url = self.get_body_argument("url", "").strip()
        method = self.get_body_argument("method", "GET").strip().upper()
        response_format = self.get_body_argument("response_format", "JSON").strip()
        example = self.get_body_argument("example", "").strip() or None
        qps_limit = self.get_body_argument("qps_limit", "").strip()
        token_required = self.get_body_argument("token_required", "false") == "true"
        remark = self.get_body_argument("remark", "").strip() or None
        
        if not name or not url:
            self.write(json.dumps({"code": 1, "msg": "名称和URL不能为空"}))
            return
        
        if ApiInterfaceRepository.create(name, url, method, response_format, example, qps_limit, token_required, remark):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "添加失败"}))

    def _edit_interface(self):
        id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        url = self.get_body_argument("url", "").strip()
        method = self.get_body_argument("method", "GET").strip().upper()
        response_format = self.get_body_argument("response_format", "JSON").strip()
        example = self.get_body_argument("example", "").strip()
        qps_limit = self.get_body_argument("qps_limit", "").strip()
        token_required = self.get_body_argument("token_required", "").strip()
        remark = self.get_body_argument("remark", "").strip()
        
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
        if url:
            update_params["url"] = url
        if method:
            update_params["method"] = method
        if response_format:
            update_params["response_format"] = response_format
        if example is not None:
            update_params["example"] = example if example else None
        if qps_limit is not None:
            update_params["qps_limit"] = qps_limit if qps_limit else None
        if token_required != "":
            update_params["token_required"] = token_required == "true"
        if remark is not None:
            update_params["remark"] = remark if remark else None
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if ApiInterfaceRepository.update(id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败"}))

    def _delete_interface(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ApiInterfaceRepository.delete(id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete(self):
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的接口"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        deleted_count = ApiInterfaceRepository.batch_delete(ids)
        self.write(json.dumps({
            "code": 0,
            "msg": f"成功删除 {deleted_count} 条记录"
        }))
