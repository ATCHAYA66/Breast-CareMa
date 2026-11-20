"""Check uvicorn output."""
import subprocess
import sys
import time

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(4)
proc.terminate()
stdout, stderr = proc.communicate(timeout=5)
print("STDOUT:", stdout)
print("STDERR:", stderr)
