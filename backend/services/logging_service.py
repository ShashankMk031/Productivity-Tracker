import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
TODO_PATH = BASE_DIR / "TODO.md"

def ensure_logs_dir():
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log_error(component: str, message: str):
    ensure_logs_dir()
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [ERROR] [{component}] {message}\n"
    
    with open(LOGS_DIR / "system.log", "a") as f:
        f.write(log_line)

def log_critical(component: str, message: str):
    ensure_logs_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [CRITICAL] [{component}] {message}\n"
    
    with open(LOGS_DIR / "system.log", "a") as f:
        f.write(log_line)
        
    # Append to TODO.md
    todo_entry = f"- [ ] [URGENT] {component}: {message} ({timestamp})\n"
    
    # Create TODO.md if it doesn't exist
    if not TODO_PATH.exists():
        with open(TODO_PATH, "w") as f:
            f.write("# System Maintenance TODOs\n\n")
            
    with open(TODO_PATH, "a") as f:
        f.write(todo_entry)
