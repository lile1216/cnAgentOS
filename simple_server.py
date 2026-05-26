import tornado.ioloop
import tornado.web
import os

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server is working!")

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Login Page")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/auth/login", LoginHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server started on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
