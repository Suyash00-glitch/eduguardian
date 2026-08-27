"""
Local Development Multi-Process Service Launcher.

Starts all independent A2A microservices and the FastAPI Gateway simultaneously.

Services:
  - Port 8001: Student Insight Agent A2A Microservice
  - Port 8002: Study Planner Agent A2A Microservice
  - Port 8003: Recovery Coach Agent A2A Microservice
  - Port 8000: FastAPI Gateway / Orchestrator API

Usage:
  python chatbot/run_a2a_services.py
"""
import subprocess
import sys
import time

SERVICES = [
    ("Student Insight Agent", 8001, "chatbot.backend.services.insight_service:app"),
    ("Study Planner Agent", 8002, "chatbot.backend.services.planner_service:app"),
    ("Recovery Coach Agent", 8003, "chatbot.backend.services.coach_service:app"),
]

def main():
    processes = []
    print("=" * 60)
    print("Starting EduGuardian AI Agent Services (A2A Network)")
    print("=" * 60)

    try:
        for name, port, target in SERVICES:
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                target,
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ]
            print(f"Starting {name:<24} on http://localhost:{port} (target: {target})")
            proc = subprocess.Popen(cmd)
            processes.append((name, proc))

        print("\nAll A2A agent microservices started successfully.")
        print("Press Ctrl+C to terminate services.\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down all agent services...")
        for name, proc in processes:
            print(f"Terminating {name}...")
            proc.terminate()
        for name, proc in processes:
            proc.wait()
        print("Done.")

if __name__ == "__main__":
    main()
