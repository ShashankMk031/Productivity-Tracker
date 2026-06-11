import sqlite3
from database.db import get_db
from services.report_audit_service import run_report_audit

with get_db() as db:
    run_report_audit(db)
