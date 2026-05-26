import os
import sys

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# 测试基本导入
try:
    import tornado
    print(f"Tornado version: {tornado.version}")
except ImportError as e:
    print(f"Error importing tornado: {e}")

# 测试应用导入
sys.path.insert(0, ".")
try:
    from app import make_app, init_db, init_default_users, init_admin_user
    print("Successfully imported app module")
except Exception as e:
    print(f"Error importing app module: {e}")
    import traceback
    traceback.print_exc()

print("Test completed")
