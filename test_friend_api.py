import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.db import init_db
from app.models.user import UserRepository
from app.models.friendship import FriendshipRepository

# 初始化数据库
init_db()

# 创建测试用户
print("Creating test users...")
if not UserRepository.get_user_by_username("test1"):
    UserRepository.create_user("test1", "password123")
if not UserRepository.get_user_by_username("test2"):
    UserRepository.create_user("test2", "password123")

# 获取用户列表
users = UserRepository.get_users()
print("All users:", users)

# 测试搜索功能
print("\nTesting user search...")
test1_user = UserRepository.get_user_by_username("test1")
print("test1 user:", test1_user)

# 测试添加好友
if test1_user:
    result = FriendshipRepository.send_friend_request(test1_user["id"], "test2")
    print("Friend request result:", result)
