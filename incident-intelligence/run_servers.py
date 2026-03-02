"""
Helper script to start both backend and frontend servers.
Run this from the incident-intelligence directory.
"""
import subprocess
import sys
import os
import time

base = os.path.dirname(os.path.abspath(__file__))

backend_dir = os.path.join(base, "backend")
frontend_dir = os.path.join(base, "frontend")

python_exe = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")

print("[*] Starting FastAPI backend on http://localhost:8000 ...")
backend = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    cwd=backend_dir,
)

print("[*] Starting Vite frontend on http://localhost:5173 ...")
frontend = subprocess.Popen(
    ["npm.cmd", "run", "dev"],
    cwd=frontend_dir,
    shell=False,
)

print("[*] Both servers started.")
print("    Backend:  http://localhost:8000")
print("    Frontend: http://localhost:5173")
print("[*] Press Ctrl+C to stop both servers.")

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    print("\n[*] Stopping servers...")
    backend.terminate()
    frontend.terminate()
    sys.exit(0)
