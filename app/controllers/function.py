import tornado.web

from app.controllers.base import BaseHandler

class FunctionListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("function_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class ModuleListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("module_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class FunctionApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.write({"code": 0, "msg": "success", "data": []})

class ModuleApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.write({"code": 0, "msg": "success", "data": []})
