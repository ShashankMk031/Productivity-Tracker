
"""
Productivity Tracker - FastAPI Backend
Phase 3 Prep: Service Layer Refactor
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from config import BASE_DIR, FRONTEND_DIR
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
from routes.daily_notes import router as daily_notes_router
from services.logging_service import get_logger

logger = get_logger(__name__)

async def run_maintenance_tasks():
    logger.info("[Lifespan] Starting background maintenance tasks...")
    # Sleep 1.0s to allow the server to launch and bind
    await asyncio.sleep(1.0)
    
    from database.db import get_db
    from services.report_audit_service import run_report_audit
    from intelligence.snapshot_service import save_snapshot
    
    try:
        with get_db() as db:
            logger.info("[Lifespan] Running report audit...")
            run_report_audit(db)
            
            logger.info("[Lifespan] Running snapshot audit...")
            save_snapshot(db, "auto")
            
            logger.info("[Lifespan] Background maintenance tasks complete.")
    except Exception as e:
        logger.error("[Lifespan] Error running background maintenance tasks: %s", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Run migrations on startup
    init_db()
    
    # 2. Run database/filesystem integrity checks
    from database.db import get_db
    from services.integrity_service import run_integrity_check
    try:
        with get_db() as db:
            run_integrity_check(db)
    except Exception as e:
        logger.error("[Lifespan] Integrity check failed during startup: %s", e)
        
    # 3. Server ready (app starts serving requests)
    # 4. Spawning post-startup background maintenance task
    maintenance_task = asyncio.create_task(run_maintenance_tasks())
    
    yield
    
    # Cancel task on shutdown
    maintenance_task.cancel()
    try:
        await maintenance_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Productivity Tracker API", version="1.3.0", lifespan=lifespan)

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
app.include_router(daily_notes_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api/intelligence")
app.include_router(settings_router, prefix="/api/settings")

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    return RedirectResponse("/dashboard")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

@app.get("/tasks")
def serve_tasks():
    return FileResponse(str(FRONTEND_DIR / "tasks.html"))

@app.get("/goals")
def serve_goals():
    return FileResponse(str(FRONTEND_DIR / "goals.html"))

@app.get("/projects")
def serve_projects():
    return FileResponse(str(FRONTEND_DIR / "projects.html"))

@app.get("/insights")
def serve_insights():
    return FileResponse(str(FRONTEND_DIR / "insights.html"))

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
