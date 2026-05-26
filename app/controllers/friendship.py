import tornado.web

from app.models.friendship import FriendshipRepository, PrivateMessageRepository
from app.models.user import UserRepository


class FriendApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "list":
            self._get_friends()
        elif action == "requests":
            self._get_pending_requests()
        elif action == "search":
            self._search_users()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "add":
            self._send_friend_request()
        elif action == "accept":
            self._accept_request()
        elif action == "reject":
            self._reject_request()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_friends(self):
        user_id = self.get_current_user_id()
        if not user_id:
            user_id = 1
        
        friends = FriendshipRepository.get_friends(user_id)
        self.write({"code": 0, "data": friends})
    
    def _get_pending_requests(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        requests = FriendshipRepository.get_pending_requests(user_id)
        self.write({"code": 0, "data": requests})
    
    def _search_users(self):
        keyword = self.get_argument("keyword", "")
        if not keyword:
            self.write({"code": -1, "msg": "请输入搜索关键词"})
            return
        
        current_user_id = self.get_current_user_id()
        users = UserRepository.get_users()
        
        filtered = []
        for user in users:
            if user["id"] != current_user_id and keyword.lower() in user["username"].lower():
                is_friend = FriendshipRepository.is_friend(current_user_id, user["id"])
                filtered.append({
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "is_friend": is_friend
                })
        
        self.write({"code": 0, "data": filtered})
    
    def _send_friend_request(self):
        friend_username = self.get_argument("username", "")
        if not friend_username:
            self.write({"code": -1, "msg": "请输入用户名"})
            return
        
        current_user_id = self.get_current_user_id()
        if not current_user_id:
            current_user_id = 1
        
        result = FriendshipRepository.send_friend_request(current_user_id, friend_username)
        if result["success"]:
            self.write({"code": 0, "msg": result["msg"]})
        else:
            self.write({"code": -1, "msg": result["msg"]})
    
    def _accept_request(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        friend_id = self.get_argument("friend_id", "")
        if not friend_id:
            self.write({"code": -1, "msg": "缺少好友ID"})
            return
        
        result = FriendshipRepository.accept_friend_request(user_id, int(friend_id))
        if result["success"]:
            self.write({"code": 0, "msg": result["msg"]})
        else:
            self.write({"code": -1, "msg": result["msg"]})
    
    def _reject_request(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        friend_id = self.get_argument("friend_id", "")
        if not friend_id:
            self.write({"code": -1, "msg": "缺少好友ID"})
            return
        
        result = FriendshipRepository.reject_friend_request(user_id, int(friend_id))
        if result["success"]:
            self.write({"code": 0, "msg": result["msg"]})
        else:
            self.write({"code": -1, "msg": result["msg"]})
    
    def get_current_user_id(self):
        username = self.get_current_user()
        if not username:
            return None
        user = UserRepository.get_user_by_username(username.decode("utf-8"))
        return user["id"] if user else None


class PrivateChatApiHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
    def get(self):
        action = self.get_argument("action", "")
        
        if action == "messages":
            self._get_messages()
        elif action == "conversations":
            self._get_conversations()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def post(self):
        action = self.get_argument("action", "")
        
        if action == "send":
            self._send_message()
        else:
            self.write({"code": -1, "msg": "未知操作"})
    
    def _get_messages(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        friend_id = self.get_argument("friend_id", "")
        if not friend_id:
            self.write({"code": -1, "msg": "缺少好友ID"})
            return
        
        messages = PrivateMessageRepository.get_messages(user_id, int(friend_id))
        self.write({"code": 0, "data": messages})
    
    def _get_conversations(self):
        user_id = self.get_current_user_id()
        if not user_id:
            self.write({"code": -1, "msg": "请先登录"})
            return
        
        conversations = PrivateMessageRepository.get_conversations(user_id)
        self.write({"code": 0, "data": conversations})
    
    def _send_message(self):
        friend_id = self.get_argument("friend_id", "")
        content = self.get_argument("content", "")
        
        if not friend_id:
            self.write({"code": -1, "msg": "缺少好友ID"})
            return
        
        if not content.strip():
            self.write({"code": -1, "msg": "消息内容不能为空"})
            return
        
        user_id = self.get_current_user_id()
        if not user_id:
            user_id = 1
        
        friend_user = UserRepository.get_user_by_username(friend_id)
        if not friend_user:
            self.write({"code": -1, "msg": "用户不存在"})
            return
        
        result = PrivateMessageRepository.send_message(user_id, friend_user["id"], content)
        if result["success"]:
            self.write({"code": 0, "msg": result["msg"]})
        else:
            self.write({"code": -1, "msg": result["msg"]})
    
    def get_current_user_id(self):
        username = self.get_current_user()
        if not username:
            return None
        user = UserRepository.get_user_by_username(username.decode("utf-8"))
        return user["id"] if user else None
