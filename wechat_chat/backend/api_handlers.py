import json
import tornado.web
import os
import uuid
from wechat_chat.backend.models import (
    WechatUserRepository, 
    WechatFriendRepository, 
    WechatFriendRequestRepository,
    WechatGroupRepository,
    WechatMessageRepository
)
from wechat_chat.backend.ai_helpers.chuannong_helper import ChuannongHelper
from wechat_chat.backend.ai_helpers.weather_helper import WeatherHelper
from wechat_chat.backend.ai_helpers.soup_helper import SoupHelper
from wechat_chat.backend.file_service import WechatFileService

class WechatBaseApiHandler(tornado.web.RequestHandler):
    """API 处理器基类"""
    def get_current_user(self):
        return self.get_secure_cookie("wechat_username")

    def prepare(self):
        if not self.current_user and self.request.method != "OPTIONS":
            self.set_status(401)
            self.finish({"code": 401, "msg": "未登录"})

class WechatUploadApiHandler(WechatBaseApiHandler):
    """文件上传 API 处理器 (支持 MD5 去重)"""
    
    def post(self):
        try:
            if 'file' not in self.request.files:
                self.write({"code": 1, "msg": "未选择文件"})
                return
            
            file_meta = self.request.files['file'][0]
            # 使用文件服务保存 (自动 MD5 去重)
            file_url, filename = WechatFileService.save_file(file_meta)
            
            self.write({"code": 0, "msg": "上传成功", "data": {"url": file_url, "filename": filename}})
            
        except Exception as e:
            self.write({"code": 1, "msg": f"上传失败: {str(e)}"})

class WechatContactApiHandler(WechatBaseApiHandler):
    """通讯录 API 处理器"""
    
    def get(self):
        action = self.get_argument("action", "list")
        username = self.current_user.decode('utf-8')
        user = WechatUserRepository.get_user_by_username(username)
        
        if action == "list":
            friends = WechatFriendRepository.get_friends(user["id"])
            groups = WechatGroupRepository.get_user_groups(user["id"])
            # 返回当前用户信息以便前端展示
            me = {"id": user["id"], "username": user["username"], "nickname": user["nickname"], "avatar": user["avatar"]}
            self.write({"code": 0, "data": {"friends": friends, "groups": groups, "me": me}})
            
        elif action == "search":
            search_name = self.get_argument("username", "").strip()
            target_user = WechatUserRepository.get_user_by_username(search_name)
            if target_user:
                # 隐藏敏感信息
                data = {"id": target_user["id"], "username": target_user["username"], "nickname": target_user["nickname"], "avatar": target_user["avatar"]}
                self.write({"code": 0, "data": data})
            else:
                self.write({"code": 1, "msg": "未找到该用户"})
        
        elif action == "requests":
            requests = WechatFriendRequestRepository.get_pending_requests(user["id"])
            self.write({"code": 0, "data": requests})

    def post(self):
        try:
            data = json.loads(self.request.body)
            action = data.get("action")
            username = self.current_user.decode('utf-8')
            user = WechatUserRepository.get_user_by_username(username)
            
            if action == "send_request":
                target_id = data.get("target_id")
                msg = data.get("message", "我是 " + user["nickname"])
                WechatFriendRequestRepository.create_request(user["id"], target_id, msg)
                self.write({"code": 0, "msg": "申请已发送"})
                
            elif action == "handle_request":
                request_id = data.get("request_id")
                status = data.get("status") # 1: 同意, 2: 拒绝
                
                if status == 1:
                    # 获取申请信息以拿到双方ID
                    with get_connection() as conn:
                        req = conn.execute("SELECT * FROM wechat_friend_request WHERE id = ?", (request_id,)).fetchone()
                        if req:
                            WechatFriendRepository.add_friend(req["from_user_id"], req["to_user_id"])
                
                WechatFriendRequestRepository.update_status(request_id, status)
                self.write({"code": 0, "msg": "处理成功"})
            
            elif action == "update_me":
                nickname = data.get("nickname")
                avatar = data.get("avatar")
                with get_connection() as conn:
                    if nickname:
                        conn.execute("UPDATE wechat_user SET nickname = ? WHERE id = ?", (nickname, user["id"]))
                    if avatar:
                        conn.execute("UPDATE wechat_user SET avatar = ? WHERE id = ?", (avatar, user["id"]))
                    conn.commit()
                self.write({"code": 0, "msg": "个人信息已更新"})
        except Exception as e:
            self.write({"code": 1, "msg": str(e)})

class WechatChatApiHandler(WechatBaseApiHandler):
    """聊天 API 处理器"""
    
    def get(self):
        target_id = int(self.get_argument("target_id"))
        chat_type = self.get_argument("chat_type", "private")
        username = self.current_user.decode('utf-8')
        user = WechatUserRepository.get_user_by_username(username)
        
        messages = WechatMessageRepository.get_messages(user["id"], target_id, chat_type)
        self.write({"code": 0, "data": messages})

    def post(self):
        try:
            data = json.loads(self.request.body)
            target_id = data.get("target_id")
            chat_type = data.get("chat_type")
            content = data.get("content")
            content_type = data.get("content_type", "text") 
            
            username = self.current_user.decode('utf-8')
            user = WechatUserRepository.get_user_by_username(username)
            
            # 保存用户消息
            WechatMessageRepository.save_message(user["id"], target_id, chat_type, content, content_type)
            
            # AI 助手触发逻辑 (仅处理文本消息)
            if content_type == 'text':
                ai_reply = None
                ai_weather_type = None
                
                # 逻辑 1: @ 机器人触发 (用于群聊或私聊)
                if "@川农小助手" in content:
                    clean_input = content.replace("@川农小助手", "").strip()
                    ai_reply = ChuannongHelper.get_response(clean_input)
                    ai_user = WechatUserRepository.get_user_by_username("chuannong_helper")
                elif "@天气小助手" in content:
                    city = content.replace("@天气小助手", "").strip() or "成都"
                    weather_res = WeatherHelper.get_response(city)
                    ai_reply = weather_res["text"]
                    ai_weather_type = weather_res["weather_type"]
                    ai_user = WechatUserRepository.get_user_by_username("weather_helper")
                elif "@毒鸡汤助手" in content:
                    ai_reply = SoupHelper.get_response()
                    ai_user = WechatUserRepository.get_user_by_username("soup_helper")
                
                # 如果有 AI 回复，保存为 AI 发出的消息
                if ai_reply and ai_user:
                    # 如果是天气助手，在回复中附带特效指令
                    if ai_weather_type:
                        ai_reply = f"COMMAND:WEATHER_EFFECT:{ai_weather_type}|{ai_reply}"
                    
                    WechatMessageRepository.save_message(ai_user["id"], target_id, chat_type, ai_reply)

            self.write({"code": 0, "msg": "发送成功"})
        except Exception as e:
            self.write({"code": 1, "msg": str(e)})

class WechatGroupApiHandler(WechatBaseApiHandler):
    """群组 API 处理器"""
    
    def post(self):
        try:
            data = json.loads(self.request.body)
            name = data.get("name")
            member_ids = data.get("member_ids", [])
            
            username = self.current_user.decode('utf-8')
            user = WechatUserRepository.get_user_by_username(username)
            
            group_id = WechatGroupRepository.create_group(name, user["id"], member_ids)
            self.write({"code": 0, "msg": "群聊创建成功", "group_id": group_id})
        except Exception as e:
            self.write({"code": 1, "msg": str(e)})

# 为了方便 handle_request 中直接使用数据库，这里需要导入 get_connection
from wechat_chat.backend.db import get_connection
