"""Test live uvicorn via subprocess.Popen."""
import subprocess
import sys
import time
import requests

proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000"])
try:
    for _ in range(20):
        time.sleep(0.5)
        try:
            r = requests.get("http://127.0.0.1:8000/api/health", timeout=1)
            if r.status_code == 200:
                print("Server online:", r.json())
                break
        except Exception as e:
            pass
    else:
        print("Timeout waiting for server")
finally:
    proc.terminate()
    proc.wait(timeout=5)
    print("Server terminated successfully")
