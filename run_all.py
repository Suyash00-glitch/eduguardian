"""
EduGuardian AI — Unified Single-Terminal Runner.

Runs:
  1. A2A Agent Services (Ports 8001, 8002, 8003)
  2. FastAPI Gateway & LangGraph Orchestrator (Port 8000)
  3. Frontend React Dev Server (Port 5173)

All in the CURRENT terminal with NO extra popup windows.
Press Ctrl+C at any time to cleanly stop everything.
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "chatbot" / "frontend"
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
VENV_UVICORN = ROOT_DIR / ".venv" / "Scripts" / "uvicorn.exe"

PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
UVICORN_EXE = str(VENV_UVICORN) if VENV_UVICORN.exists() else "uvicorn"

TARGET_PORTS = (8000, 8001, 8002, 8003, 5173)
processes: list[subprocess.Popen] = []


def free_target_ports():
    """Finds and kills any processes currently listening on ports 8000-8003 and 5173."""
    my_pid = os.getpid()
    for port in TARGET_PORTS:
        try:
            if sys.platform == "win32":
                cmd = f'netstat -ano | findstr ":{port} "'
                out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
                for line in out.strip().splitlines():
                    parts = line.strip().split()
                    if "LISTENING" in parts:
                        pid = int(parts[-1])
                        if pid != my_pid and pid > 0:
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        except Exception:
            pass


def shutdown_all(signum=None, frame=None):
    print("\n[EduGuardian] Stopping all services...")
    for p in processes:
        try:
            p.terminate()
            p.kill()
        except Exception:
            pass
    free_target_ports()
    print("[EduGuardian] All services stopped cleanly.")
    sys.exit(0)


def main():
    print("=" * 65)
    print("  Starting EduGuardian AI (Single Terminal - No Popups)")
    print("=" * 65)

    # 1. Clean any lingering processes holding our ports
    print("\n[1/4] Freeing ports 8000, 8001, 8002, 8003, 5173...")
    free_target_ports()
    time.sleep(1.5)

    signal.signal(signal.SIGINT, shutdown_all)
    signal.signal(signal.SIGTERM, shutdown_all)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # 2. Start A2A Agent Services (:8001, :8002, :8003)
    print("[2/4] Starting A2A Agent Services on :8001, :8002, :8003...")
    p_a2a = subprocess.Popen(
        [PYTHON_EXE, "chatbot/run_a2a_services.py"],
        cwd=str(ROOT_DIR),
        env=env,
    )
    processes.append(p_a2a)
    time.sleep(2.5)

    # 3. Start FastAPI Gateway & LangGraph (:8000)
    print("[3/4] Starting FastAPI Gateway & Orchestrator on :8000...")
    p_api = subprocess.Popen(
        [UVICORN_EXE, "chatbot.backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(ROOT_DIR),
        env=env,
    )
    processes.append(p_api)
    time.sleep(2.0)

    # 4. Start Frontend (:5173)
    print("[4/4] Starting Frontend UI on :5173...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    p_frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        env=env,
    )
    processes.append(p_frontend)

    print("\n" + "=" * 65)
    print("  ALL SERVICES ARE RUNNING!")
    print("  - Frontend UI:  http://localhost:5173/")
    print("  - API Docs:     http://localhost:8000/docs")
    print("  - A2A Agents:   :8001, :8002, :8003")
    print("  Press Ctrl+C to stop all services at once.")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown_all()


if __name__ == "__main__":
    main()
