import tornado.web

from app.controllers.base import BaseHandler

class PermissionListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("permission_list.html", current_user=self.current_user, xsrf_token=xsrf_token)

class PermissionApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.write({"code": 0, "msg": "success", "data": []})
