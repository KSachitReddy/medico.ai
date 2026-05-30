#!/usr/bin/env python3
"""
start.py — Start both backend and frontend with a single command.
Usage:  python start.py
"""
import subprocess
import sys
import os
import time
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))


def stream(proc, label):
    for line in proc.stdout:
        print(f"[{label}] {line}", end="")


def main():
    # Force UTF-8 encoding on standard output/error to handle emojis on all systems
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 60)
    print("  Medico.AI — Starting up")
    print("=" * 60)

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    t_back = threading.Thread(target=stream, args=(backend, "API"), daemon=True)
    t_back.start()

    print("[start.py] Waiting for backend to initialise…")
    time.sleep(4)

    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501", "--server.address", "0.0.0.0"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    t_front = threading.Thread(target=stream, args=(frontend, "UI"), daemon=True)
    t_front.start()

    print()
    print("=" * 60)
    print("  ✅  Medico.AI is running!")
    print("  📊  UI  →  http://localhost:8501")
    print("  🔌  API →  http://localhost:8000/docs")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n[start.py] Shutting down…")
        backend.terminate()
        frontend.terminate()


if __name__ == "__main__":
    main()
