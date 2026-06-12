"""
Central logging for the backend.

Standard: obtain a logger with get_logger(__name__) and use stdlib logging
levels instead of print(). log_error()/log_critical() additionally persist
to logs/system.log (and TODO.md for critical issues), preserving the
previous file-sink behavior.
"""

import logging
from datetime import datetime

from config import BASE_DIR, LOGS_DIR

TODO_PATH = BASE_DIR / "TODO.md"

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root():
    global _configured
    if _configured:
        return
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger using the one shared logging configuration."""
    _configure_root()
    return logging.getLogger(name)


def ensure_logs_dir():
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_error(component: str, message: str):
    get_logger(component).error(message)
    ensure_logs_dir()
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [ERROR] [{component}] {message}\n"

    with open(LOGS_DIR / "system.log", "a") as f:
        f.write(log_line)


def log_critical(component: str, message: str):
    get_logger(component).critical(message)
    ensure_logs_dir()
    timestamp = datetime.now().strftime(DATE_FORMAT)
    log_line = f"[{timestamp}] [CRITICAL] [{component}] {message}\n"

    with open(LOGS_DIR / "system.log", "a") as f:
        f.write(log_line)

    # Append to TODO.md so critical issues surface for the maintainer
    todo_entry = f"- [ ] [URGENT] {component}: {message} ({timestamp})\n"

    if not TODO_PATH.exists():
        with open(TODO_PATH, "w") as f:
            f.write("# System Maintenance TODOs\n\n")

    with open(TODO_PATH, "a") as f:
        f.write(todo_entry)
