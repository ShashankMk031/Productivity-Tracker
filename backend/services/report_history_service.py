import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from services.date_service import get_logical_date_ist
from services.analytics_service import aggregate_analytics
from services.logging_service import get_logger
from ai.context_builder import build_ai_context
from ai.prompt_builder import build_ai_prompt
from ai.ai_service import AIService
from intelligence.snapshot_service import save_snapshot
from services.backup_service import create_backup
from config import REPORTS_DIR as REPORTS_BASE_DIR
from config import AI_REPORTS_DIR as AI_REPORTS_BASE_DIR
from config import AI_CONTEXT_DIR as AI_CONTEXT_BASE_DIR

logger = get_logger(__name__)

def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def get_report_history(db: sqlite3.Connection):
    rows = db.execute("SELECT id, type, generated_at, summary, period_start, period_end FROM reports ORDER BY generated_at DESC").fetchall()
    return [dict(row) for row in rows]

def get_report_markdown(db: sqlite3.Connection, report_id: int):
    row = db.execute("SELECT markdown_path FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return None
    
    path = row["markdown_path"]
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

def generate_and_save_report(db: sqlite3.Connection, report_type: str, report_date = None, replace_report_id: int | None = None):
    """Generate a report and persist its artifacts and DB row.

    When replace_report_id is provided, the existing reports row is updated
    in place instead of inserting a new one. This is the regeneration path
    for reports whose AI section previously failed.
    """
    # Persist the intelligence snapshot before generating report
    try:
        save_snapshot(db, report_type)
    except Exception as e:
        logger.warning("Failed to save intelligence snapshot: %s", e)
        
    # Trigger a backup before monthly reports
    if report_type == "monthly":
        try:
            create_backup("monthly_report_pre_generation")
        except Exception as e:
            logger.warning("Failed to create pre-generation backup: %s", e)

    analytics = aggregate_analytics(db)
    metrics = analytics.get("metrics", {})
    
    # Calculate target logical date
    if report_date is None:
        today = get_logical_date_ist()
        if report_type == "monthly":
            # Last day of previous month
            first_of_current = today.replace(day=1)
            logical_today = first_of_current - timedelta(days=1)
        else:
            # Sunday of previous week
            logical_today = today - timedelta(days=today.weekday() + 1)
    else:
        # Support string parsing if a string date is provided
        if isinstance(report_date, str):
            from datetime import date
            logical_today = date.fromisoformat(report_date)
        else:
            logical_today = report_date
            
    generated_at = datetime.now().isoformat()
    
    year_str = logical_today.strftime("%Y")
    month_str = logical_today.strftime("%B")
    month_lower = logical_today.strftime("%b").lower() # e.g., may
    
    report_folder = REPORTS_BASE_DIR / year_str / month_str
    ensure_dir(report_folder)
    
    if report_type == "monthly":
        filename = f"{month_lower}_{year_str}_monthly_report.md"
        period_start = logical_today.replace(day=1).isoformat()
    else:
        week_num = (logical_today.day - 1) // 7 + 1
        filename = f"{month_lower}_week_{week_num}_report.md"
        period_start = (logical_today - timedelta(days=6)).isoformat()
        
    filepath = report_folder / filename
    period_end = logical_today.isoformat()

    # 1. Trigger behavior and note context extraction
    ai_context = build_ai_context(db, period_type=report_type, period_start=period_start, period_end=period_end)
    
    # 2. Build structured LLM Prompt
    ai_prompt = build_ai_prompt(ai_context)
    
    # 3. Generate mock/live AI Reflection (Phase 4A & 4B)
    ai_service = AIService()
    ai_reflection = ai_service.generate_reflection(ai_prompt)
    
    # 4. Save snapshots to ai_context/YYYY/
    ai_context_folder = AI_CONTEXT_BASE_DIR / year_str
    ensure_dir(ai_context_folder)
    
    if report_type == "monthly":
        context_filename = f"{month_lower}_{year_str}_monthly_context.json"
        prompt_filename = f"{month_lower}_{year_str}_monthly_prompt.txt"
    else:
        context_filename = f"{month_lower}_week_{week_num}_context.json"
        prompt_filename = f"{month_lower}_week_{week_num}_prompt.txt"
        
    context_filepath = ai_context_folder / context_filename
    prompt_filepath = ai_context_folder / prompt_filename
    
    with open(context_filepath, "w") as f:
        json.dump(ai_context.model_dump(), f, indent=2)
        
    with open(prompt_filepath, "w") as f:
        f.write(ai_prompt)
        
    logger.info("AI context snapshot saved at %s", context_filepath)
    logger.info("AI rendered prompt saved at %s", prompt_filepath)

    # Calculate scores and focus hours for Markdown inclusion
    from services.scoring_service import calculate_productivity_scores
    scores = calculate_productivity_scores(db)
    
    focus_row = db.execute(
        "SELECT SUM(duration) as total_duration FROM focus_sessions WHERE start_time >= ? AND start_time <= ?",
        (f"{period_start}T00:00:00", f"{period_end}T23:59:59")
    ).fetchone()
    focus_sec = focus_row["total_duration"] if focus_row and focus_row["total_duration"] is not None else 0
    focus_hours = round(focus_sec / 3600.0, 1)

    # Generate markdown content
    title = f"{report_type.capitalize()} Report"
    
    md_content = f"# {title} - {period_end}\n"
    md_content += f"### Period: {period_start} to {period_end}\n\n"
    md_content += "## Productivity Metrics\n"
    md_content += f"- **Completion Rate:** {metrics.get('completion_pct', 0)}%\n"
    md_content += f"- **Current Streak:** {metrics.get('current_streak', 0)} days\n"
    md_content += f"- **Longest Streak:** {metrics.get('longest_streak', 0)} days\n"
    md_content += f"- **Active Tasks:** {metrics.get('active_tasks', 0)}\n"
    md_content += f"- **Focused Work:** {focus_hours} hours\n"
    md_content += f"- **Consistency Score:** {scores.get('consistency', 0)}/100\n"
    md_content += f"- **Execution Score:** {scores.get('execution', 0)}/100\n"
    md_content += f"- **Goal Progress Score:** {scores.get('goal_progress', 0)}/100\n\n"
    
    md_content += "## AI Reflection & Analysis\n"
    md_content += ai_reflection + "\n\n"
    
    md_content += "---\n*This report was automatically generated by your Productivity Tracker.*\n"
    
    with open(filepath, "w") as f:
        f.write(md_content)

    # Save raw AI response to /ai_reports/{Year}/{Month}/{filename}
    ai_reports_folder = AI_REPORTS_BASE_DIR / year_str / month_str
    ensure_dir(ai_reports_folder)
    
    if report_type == "monthly":
        raw_filename = f"{month_lower}_monthly_ai_response.txt"
    else:
        raw_filename = f"{month_lower}_week_{week_num}_ai_response.txt"
        
    raw_filepath = ai_reports_folder / raw_filename
    with open(raw_filepath, "w") as f:
        f.write(ai_reflection)
    logger.info("Raw AI response saved at %s", raw_filepath)
        
    summary = f"Completion: {metrics.get('completion_pct', 0)}% | Streak: {metrics.get('current_streak', 0)}"
    
    # Store in DB (update in place when regenerating a failed report)
    if replace_report_id is not None:
        db.execute(
            "UPDATE reports SET type = ?, generated_at = ?, markdown_path = ?, summary = ?, period_start = ?, period_end = ? WHERE id = ?",
            (report_type, generated_at, str(filepath), summary, period_start, period_end, replace_report_id)
        )
        report_id = replace_report_id
    else:
        cur = db.execute(
            "INSERT INTO reports (type, generated_at, markdown_path, summary, period_start, period_end) VALUES (?, ?, ?, ?, ?, ?)",
            (report_type, generated_at, str(filepath), summary, period_start, period_end)
        )
        report_id = cur.lastrowid
    
    return {
        "id": report_id,
        "type": report_type,
        "generated_at": generated_at,
        "summary": summary,
        "markdown_content": md_content,
        "ai_reflection": ai_reflection
    }

def get_report_ai_reflection(db: sqlite3.Connection, report_id: int):
    row = db.execute("SELECT type, markdown_path FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return None
    
    markdown_path = Path(row["markdown_path"])
    report_type = row["type"]
    
    parts = markdown_path.parts
    if len(parts) < 3:
        return None
    year_str = parts[-3]
    month_str = parts[-2]
    filename = parts[-1]
    
    if report_type == "monthly":
        month_lower = filename.split("_")[0]
        raw_filename = f"{month_lower}_monthly_ai_response.txt"
    else:
        raw_filename = filename.replace("_report.md", "_ai_response.txt")
        
    ai_filepath = AI_REPORTS_BASE_DIR / year_str / month_str / raw_filename
    if ai_filepath.exists():
        with open(ai_filepath, "r") as f:
            return f.read()
            
    return None

def report_ai_failed(db: sqlite3.Connection, report_id: int) -> bool:
    """True when the stored report's AI section is missing or is the failure placeholder.

    Used by the report routes to allow regeneration instead of permanently
    blocking a period behind a failed report.
    """
    from ai.ai_service import is_failed_reflection
    return is_failed_reflection(get_report_ai_reflection(db, report_id))
