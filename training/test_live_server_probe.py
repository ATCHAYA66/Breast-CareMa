"""Probe live uvicorn server in the same command."""
import os
import subprocess
import sys
import time
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env["PYTHONPATH"] = str(PROJECT_ROOT)

print("Launching uvicorn subprocess...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--log-level", "info"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    cwd=str(PROJECT_ROOT),
    env=env
)

# Start a reader thread to print server logs in real time
import threading
def reader():
    for line in proc.stdout:
        print("[UVICORN]", line, end="")
t = threading.Thread(target=reader, daemon=True)
t.start()

try:
    print("Waiting for server to respond on http://127.0.0.1:8000/api/health...")
    for i in range(25):
        time.sleep(0.5)
        try:
            r = requests.get("http://127.0.0.1:8000/api/health", timeout=1)
            if r.status_code == 200:
                print(f"\nSUCCESS! Server responded in {(i+1)*0.5:.1f}s:", r.json())
                break
        except Exception as ex:
            pass
    else:
        print("\nTimeout waiting for server.")
finally:
    print("Shutting down uvicorn subprocess...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Done.")
