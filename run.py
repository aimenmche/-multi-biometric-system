#!/usr/bin/env python3
"""
Multi-Biometric Identity Verification System
Startup script - seeds database and launches the server.
"""

import subprocess
import sys
import os
import time
import webbrowser


def main():
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")

    print("=" * 60)
    print("  Multi-Biometric Identity Verification System")
    print("=" * 60)
    print()

    os.chdir(backend_dir)

    print("[1/3] Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=False,
    )

    print()
    print("[2/3] Seeding database...")
    seed_result = subprocess.run(
        [sys.executable, "seed.py"],
        capture_output=True,
        text=True,
    )
    print(seed_result.stdout)
    if seed_result.stderr:
        print(seed_result.stderr)

    print()
    print("[3/3] Starting server...")
    print()
    print("  Server: http://localhost:8000")
    print("  Frontend: http://localhost:8000/static/index.html")
    print()
    print("  Default credentials:")
    print("    Admin:   admin / admin123")
    print("    Student: student1 / student123")
    print()
    print("  Press Ctrl+C to stop the server.")
    print()

    webbrowser.open("http://localhost:8000/static/index.html")

    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
