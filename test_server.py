import tornado.ioloop
import tornado.web
import os

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server is running!")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ],
    static_path=os.path.join(os.path.dirname(__file__), "app", "static"),
    template_path=os.path.join(os.path.dirname(__file__), "app", "templates"),
    debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(10086)
    print("Server started on http://localhost:10086")
    tornado.ioloop.IOLoop.current().start()
