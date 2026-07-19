import os
import sys
import subprocess
import socket
import shutil
import time

def print_header(title):
    print("=" * 60)
    print(f" Chronos CLI: {title}")
    print("=" * 60)

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_doctor():
    print_header("System Health Check (Doctor)")
    issues = 0

    # 1. Check Python
    print(f"[ OK ] Python Version: {sys.version.split()[0]}")

    # 2. Check Node
    node_ver = shutil.which("node")
    if node_ver:
        try:
            node_out = subprocess.check_output(["node", "--version"]).decode().strip()
            print(f"[ OK ] Node.js Version: {node_out}")
        except Exception:
            print("[FAIL] Node.js is installed but failed to run.")
            issues += 1
    else:
        print("[FAIL] Node.js not found in PATH (Frontend requires Node.js).")
        issues += 1

    # 3. Check SQLite database file
    db_path = os.path.abspath("backend/chronos.db")
    if os.path.exists(db_path):
        print(f"[ OK ] Local SQLite DB detected: {db_path} ({os.path.getsize(db_path)} bytes)")
    else:
        print("[WARN] Local SQLite DB not initialized yet. Run 'python chronos-cli.py init'.")

    # 4. Check Ports availability
    if is_port_open(8000):
        print("[WARN] Port 8000 (Backend API) is already in use.")
    else:
        print("[ OK ] Port 8000 (Backend API) is available.")

    if is_port_open(5173):
        print("[WARN] Port 5173 (Vite Frontend) is already in use.")
    else:
        print("[ OK ] Port 5173 (Vite Frontend) is available.")

    print("=" * 60)
    if issues == 0:
        print("Doctor Result: All checks passed. Ready to launch!")
    else:
        print(f"Doctor Result: Found {issues} issue(s) that might disrupt local execution.")

def run_init():
    print_header("Initializing Database Schemas")
    db_path = "backend/chronos.db"
    
    # Release any existing locks by ensuring file can be deleted
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("[ OK ] Deleted existing SQLite database to trigger a clean slate reset.")
        except Exception as e:
            print(f"[FAIL] Failed to delete existing database. Is a server running? Error: {e}")
            return

    # Add paths and invoke schema creations
    sys.path.append(os.path.abspath("backend"))
    try:
        from app.db.session import engine
        from app.models.base import Base
        import app.models.span
        import app.models.trace
        
        Base.metadata.create_all(bind=engine)
        print(f"[ OK ] Database tables successfully created inside: {os.path.abspath(db_path)}")
    except Exception as e:
        print(f"[FAIL] Database schema initialization failed: {e}")

def run_local_services():
    print_header("Launching Local Services (FastAPI + React)")
    processes = []
    
    try:
        # Start Backend Server
        print("[INFO] Booting FastAPI backend on http://localhost:8000 ...")
        backend_proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=os.path.abspath("backend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(backend_proc)
        
        # Give backend 1.5 seconds to bind to port
        time.sleep(1.5)
        if backend_proc.poll() is not None:
            print("[FAIL] Backend failed to start. Run 'python chronos-cli.py doctor' to check ports.")
            return

        # Start Frontend Dev Server
        print("[INFO] Booting React Vite dashboard on http://localhost:5173 ...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=os.path.abspath("frontend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
        processes.append(frontend_proc)
        
        print("\n[ OK ] Both services are running successfully!")
        print("Press Ctrl+C to terminate both servers concurrently.")
        
        # Keep running until Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Intercepted shutdown signal. Cleaning up subprocesses...")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                p.kill()
        print("[ OK ] Both servers stopped.")

def run_telemetry_benchmark():
    print_header("Running Ingestion Benchmarks")
    try:
        subprocess.run([sys.executable, "scripts/benchmark.py"], cwd=os.path.abspath("."))
    except Exception as e:
        print(f"[FAIL] Benchmark failed: {e}")

def print_help():
    print("Usage: python chronos-cli.py [command]")
    print("\nCommands:")
    print("  init      - Reset local database file and create schemas")
    print("  run       - Launch backend (FastAPI) and frontend (Vite React) servers concurrently")
    print("  benchmark - Trigger telemetry benchmark testing suite")
    print("  doctor    - Inspect system environment and diagnostic port mapping dependencies")
    print("  help      - Print this usage screen")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "init":
        run_init()
    elif cmd == "run":
        run_local_services()
    elif cmd == "benchmark":
        run_telemetry_benchmark()
    elif cmd == "doctor":
        run_doctor()
    else:
        print_help()
