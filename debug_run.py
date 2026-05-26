import subprocess
import os

os.chdir(r'c:\Users\47146\cnAgentOS')
result = subprocess.run(['python', 'app.py'], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
