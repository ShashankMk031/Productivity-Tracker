
"""
Productivity Tracker - FastAPI Backend
Phase 3 Prep: Service Layer Refactor
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from database.db import init_db
from routes.tasks import router as tasks_router
from routes.reports import router as reports_router
from routes.goals import router as goals_router
from routes.projects import router as projects_router
from routes.scores import router as scores_router
from routes.focus import router as focus_router
from routes.reminders import router as reminders_router
from routes.intelligence import router as intelligence_router
from routes.settings import router as settings_router

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Productivity Tracker API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(goals_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(scores_router, prefix="/api")
app.include_router(focus_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api/intelligence")
app.include_router(settings_router, prefix="/api/settings")

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.on_event("startup")
def startup():
    # Single schema authority: init_db() runs the unified migration runner
    # (backend/database/migrations.py).
    init_db()
    from database.db import get_db
    from services.report_audit_service import run_report_audit
    from services.integrity_service import run_integrity_check
    with get_db() as db:
        run_integrity_check(db)
        run_report_audit(db)

@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/reports")
def serve_reports():
    return FileResponse(str(FRONTEND_DIR / "reports.html"))

@app.get("/calendar")
def serve_calendar():
    return FileResponse(str(FRONTEND_DIR / "calendar.html"))

@app.get("/settings")
def serve_settings():
    return FileResponse(str(FRONTEND_DIR / "settings.html"))

@app.get("/favicon.ico")
def serve_favicon():
    return FileResponse(str(FRONTEND_DIR / "favicon.svg"), media_type="image/svg+xml")

@app.get("/ai_reports")
def list_ai_reports():
    ai_reports_dir = BASE_DIR / "ai_reports"
    if not ai_reports_dir.exists():
        return {"reports": []}
    
    txt_files = list(ai_reports_dir.rglob("*.txt"))
    reports_list = [str(f.relative_to(ai_reports_dir)) for f in txt_files]
    return {"reports": sorted(reports_list, reverse=True)}

@app.get("/ai_reports/{year}/{month}/{filename}")
def serve_ai_report(year: str, month: str, filename: str):
    file_path = BASE_DIR / "ai_reports" / year / month / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="AI report file not found")
    return FileResponse(str(file_path))
