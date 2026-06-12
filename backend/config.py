"""
Central configuration: single source of truth for filesystem paths and
timezone settings.

Before this module existed, BASE_DIR and the artifact directory paths were
re-derived independently in six or more modules (a root cause of the
storage-dashboard DB-path bug fixed in Sprint 1). All path and timezone
constants now live here; modules import from config instead of computing
their own.
"""

from pathlib import Path
from zoneinfo import ZoneInfo

# Project root (this file lives in backend/)
BASE_DIR = Path(__file__).parent.parent

# Database
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "tracker.db"

# Artifact directories
REPORTS_DIR = BASE_DIR / "reports"
AI_REPORTS_DIR = BASE_DIR / "ai_reports"
AI_CONTEXT_DIR = BASE_DIR / "ai_context"
SNAPSHOT_DIR = BASE_DIR / "intelligence_snapshots"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"

# Frontend
FRONTEND_DIR = BASE_DIR / "frontend"

# AI configuration
AI_ENV_PATH = Path(__file__).parent / ".env"

# Timezone / logical-day settings (IST day rollover at 04:00)
TIMEZONE = ZoneInfo("Asia/Kolkata")
DAY_RESET_HOUR = 4
DAY_RESET_LABEL = "Day resets at 04:00 AM (IST)"
