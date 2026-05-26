import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository


class FriendChatHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/auth/user/login")
            return
        
        user = UserRepository.get_user_by_username(self.current_user)
        if not user:
            self.redirect("/auth/user/login")
            return
        
        xsrf_token = self.xsrf_token.decode('utf-8')
        
        self.render("friend_chat.html", 
                    current_user=self.current_user, 
                    xsrf_token=xsrf_token)
