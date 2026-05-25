import tornado.web

from app.controllers.base import BaseHandler

class AdminHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin.html", current_user=self.current_user)

class WelcomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("welcome.html")

class IndexHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect("/admin")
        else:
            self.redirect("/auth/login")