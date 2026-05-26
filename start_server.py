import subprocess
import os

os.chdir(r'c:\Users\47146\cnAgentOS')
# 使用单进程模式启动，避免多进程问题
subprocess.run(['python', '-c', '''
import sys
sys.path.insert(0, ".")
from app import *
init_db()
init_default_users()
init_admin_user()
init_scout_sources()
init_api_interfaces()
init_digital_employees()
init_sentiment_samples()

app = make_app()
app.listen(10086)
print("Server started on port 10086", flush=True)
tornado.ioloop.IOLoop.current().start()
'''], shell=True)