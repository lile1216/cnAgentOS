import os
os.chdir(r'c:\Users\47146\cnAgentOS')

# 简单测试导入
print("Testing imports...")
try:
    from app.models.db import init_db, get_connection
    print("db.py imported successfully")
except Exception as e:
    print(f"Error importing db.py: {e}")

try:
    from app.models.user import UserRepository
    print("user.py imported successfully")
except Exception as e:
    print(f"Error importing user.py: {e}")

try:
    from app.models.friendship import FriendshipRepository
    print("friendship.py imported successfully")
except Exception as e:
    print(f"Error importing friendship.py: {e}")

try:
    from app.models.digital_employee import DigitalEmployeeManager
    print("digital_employee.py imported successfully")
except Exception as e:
    print(f"Error importing digital_employee.py: {e}")

print("\nTesting digital employees...")
employees = DigitalEmployeeManager.list_employees()
print(f"Available employees: {employees}")

for emp_name in employees:
    emp = DigitalEmployeeManager.get_employee(emp_name)
    print(f"{emp_name}: {emp.respond('你好')}")
