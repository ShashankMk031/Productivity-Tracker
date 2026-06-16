import json
import sqlite3
from datetime import datetime, timedelta

from services.date_service import get_logical_date_ist, task_active_on_date
from utils.helpers import serialize_task

RISK_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _safe_json(value):
    try:
        return json.loads(value) if value else {}
    except json.JSONDecodeError:
        return {}


def persist_predictions(
    db: sqlite3.Connection,
    snapshot: dict,
    snapshot_path: str | None = None,
    report_period: str = "manual",
):
    predicted_on = snapshot.get("generated_at") or datetime.now().isoformat()

    rows = []
    burnout = snapshot.get("burnout")
    if burnout:
        rows.append(("burnout", "system", None, "Burnout", 7, burnout))

    focus = snapshot.get("focus")
    if focus:
        rows.append(("focus", "system", None, "Focus Effectiveness", 7, focus))

    for item in snapshot.get("habits", []):
        rows.append(("consistency", "task", item.get("task_id"), item.get("task_title", "Habit"), 7, item))

    for item in snapshot.get("deadlines", []):
        rows.append(("deadline", "project", item.get("project_id"), item.get("project_title", "Project"), 14, item))

    for item in snapshot.get("goals", []):
        rows.append(("goal", "goal", item.get("goal_id"), item.get("goal_title", "Goal"), 14, item))

    for predictor_type, target_type, target_id, target_label, horizon_days, item in rows:
        db.execute(
            """
            INSERT OR IGNORE INTO prediction_records (
                predictor_type, target_type, target_id, target_label,
                predicted_on, snapshot_path, report_period, horizon_days,
                predicted_risk, confidence, reason, supporting_metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                predictor_type,
                target_type,
                target_id,
                target_label,
                predicted_on,
                snapshot_path,
                report_period,
                horizon_days,
                item.get("risk_level", "LOW"),
                int(item.get("confidence", 0) or 0),
                item.get("reason", ""),
                json.dumps(item.get("supporting_metrics", {})),
            ),
        )


def _risk_score(predicted: str, actual: str) -> tuple[float, str]:
    predicted_rank = RISK_SCORE.get(predicted, 1)
    actual_rank = RISK_SCORE.get(actual, 1)
    delta = abs(predicted_rank - actual_rank)
    if delta == 0:
        return 1.0, "Correct"
    if delta == 1:
        return 0.5, "Near miss"
    return 0.0, "Missed risk"


def _fetch_task(db: sqlite3.Connection, task_id: int):
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return serialize_task(row) if row else None


def _completion_rate_for_task(db: sqlite3.Connection, task_id: int, start_date, end_date) -> tuple[float, int]:
    task = _fetch_task(db, task_id)
    if not task:
        return 0.0, 0
    total = 0
    done = 0
    current = start_date
    while current <= end_date:
        if task_active_on_date(task, current):
            total += 1
            row = db.execute(
                "SELECT completed FROM daily_entries WHERE task_id = ? AND date = ?",
                (task_id, current.isoformat()),
            ).fetchone()
            if row and row["completed"]:
                done += 1
        current += timedelta(days=1)
    if not total:
        return 0.0, 0
    return (done / total) * 100, total


def _burnout_window_risk(db: sqlite3.Connection, start_date, end_date) -> tuple[str, str]:
    notes = db.execute(
        "SELECT note FROM daily_entries WHERE date >= ? AND date <= ? AND note != ''",
        (start_date.isoformat(), end_date.isoformat()),
    ).fetchall()
    focus_rows = db.execute(
        "SELECT duration, notes FROM focus_sessions WHERE start_time >= ? AND start_time <= ?",
        (f"{start_date.isoformat()}T00:00:00", f"{end_date.isoformat()}T23:59:59"),
    ).fetchall()
    fatigue_terms = ("tired", "exhausted", "burnout", "fatigue", "drained", "overwhelmed", "stress")
    fatigue_hits = sum(1 for row in notes if any(term in (row["note"] or "").lower() for term in fatigue_terms))
    fatigue_hits += sum(1 for row in focus_rows if any(term in (row["notes"] or "").lower() for term in fatigue_terms))
    missed = db.execute(
        "SELECT COUNT(*) AS c FROM daily_entries WHERE date >= ? AND date <= ? AND completed = 0",
        (start_date.isoformat(), end_date.isoformat()),
    ).fetchone()["c"]
    if fatigue_hits >= 3 or missed >= 6:
        return "HIGH", f"Fatigue spike ({fatigue_hits}) and missed tasks ({missed})"
    if fatigue_hits >= 1 or missed >= 3:
        return "MEDIUM", f"Moderate fatigue pressure ({fatigue_hits}) and missed tasks ({missed})"
    return "LOW", "Stable workload signals"


def _focus_window_risk(db: sqlite3.Connection, best_range: str, start_date, end_date) -> tuple[str, str]:
    sessions = db.execute(
        "SELECT duration FROM focus_sessions WHERE start_time >= ? AND start_time <= ?",
        (f"{start_date.isoformat()}T00:00:00", f"{end_date.isoformat()}T23:59:59"),
    ).fetchall()
    if not sessions:
        return "MEDIUM", "No focus sessions recorded during evaluation window"
    durations = [row["duration"] / 60 for row in sessions]
    avg = sum(durations) / len(durations)
    if "Optimal" in best_range and 50 <= avg <= 70:
        return "LOW", f"Average focus duration stayed aligned at {avg:.0f} minutes"
    if "Medium" in best_range and 30 <= avg <= 50:
        return "LOW", f"Average focus duration stayed aligned at {avg:.0f} minutes"
    if avg < 25 or avg > 95:
        return "HIGH", f"Average focus duration drifted to {avg:.0f} minutes"
    return "MEDIUM", f"Average focus duration drifted to {avg:.0f} minutes"


def _deadline_actual_risk(db: sqlite3.Connection, target_id: int | None, label: str) -> tuple[str, str] | None:
    row = None
    if target_id is not None:
        row = db.execute("SELECT * FROM projects WHERE id = ?", (target_id,)).fetchone()
    if row is None:
        row = db.execute("SELECT * FROM projects WHERE title = ?", (label,)).fetchone()
    if not row:
        return "HIGH", "Project no longer exists"
    deadline = datetime.fromisoformat(row["deadline"]).date()
    today = get_logical_date_ist()
    completed_at = row["completed_at"]
    if row["completed"]:
        if completed_at:
            completed_date = datetime.fromisoformat(completed_at).date()
            if completed_date <= deadline:
                return "LOW", "Completed on time"
            return "HIGH", "Completed late"
        return ("LOW", "Completed") if deadline >= today else ("HIGH", "Completed after deadline window")
    if deadline < today:
        return "HIGH", "Deadline missed"
    if (deadline - today).days <= 3 and row["progress"] < 80:
        return "MEDIUM", "Deadline close with incomplete progress"
    return None


def _goal_actual_risk(db: sqlite3.Connection, target_id: int | None, label: str) -> tuple[str, str] | None:
    row = None
    if target_id is not None:
        row = db.execute("SELECT * FROM goals WHERE id = ?", (target_id,)).fetchone()
    if row is None:
        row = db.execute("SELECT * FROM goals WHERE title = ?", (label,)).fetchone()
    if not row:
        return "HIGH", "Goal no longer exists"
    today = get_logical_date_ist()
    if row["completed"]:
        if row["target_date"] and datetime.fromisoformat(row["target_date"]).date() < today:
            return "HIGH", "Completed after target date"
        return "LOW", "Completed"
    if row["target_date"]:
        target = datetime.fromisoformat(row["target_date"]).date()
        if target < today:
            return "HIGH", "Target date passed"
        if (target - today).days <= 7 and row["progress"] < 75:
            return "MEDIUM", "Target date approaching with incomplete progress"
        return None
    return ("MEDIUM", "Progress remains slow") if row["progress"] < 40 else ("LOW", "Progress remains healthy")


def _evaluate_record(db: sqlite3.Connection, row) -> tuple[str, str, float, str] | None:
    predicted_on = datetime.fromisoformat(row["predicted_on"])
    start_date = predicted_on.date() + timedelta(days=1)
    end_date = predicted_on.date() + timedelta(days=row["horizon_days"])
    today = get_logical_date_ist()
    if end_date > today and row["predictor_type"] in {"burnout", "consistency", "focus"}:
        return None

    predictor = row["predictor_type"]
    target_label = row["target_label"]
    metrics = _safe_json(row["supporting_metrics_json"])

    if predictor == "burnout":
        actual_risk, actual_outcome = _burnout_window_risk(db, start_date, min(end_date, today))
    elif predictor == "consistency":
        if row["target_id"] is None:
            return None
        completion_rate, sample_size = _completion_rate_for_task(db, row["target_id"], start_date, min(end_date, today))
        if sample_size == 0:
            return None
        if completion_rate < 35:
            actual_risk, actual_outcome = "HIGH", f"Task completion fell to {completion_rate:.0f}%"
        elif completion_rate < 65:
            actual_risk, actual_outcome = "MEDIUM", f"Task completion held at {completion_rate:.0f}%"
        else:
            actual_risk, actual_outcome = "LOW", f"Task completion held at {completion_rate:.0f}%"
    elif predictor == "deadline":
        result = _deadline_actual_risk(db, row["target_id"], target_label)
        if result is None:
            return None
        actual_risk, actual_outcome = result
    elif predictor == "goal":
        result = _goal_actual_risk(db, row["target_id"], target_label)
        if result is None:
            return None
        actual_risk, actual_outcome = result
    elif predictor == "focus":
        actual_risk, actual_outcome = _focus_window_risk(db, target_label, start_date, min(end_date, today))
    else:
        return None

    score, label = _risk_score(row["predicted_risk"], actual_risk)
    return actual_outcome, actual_risk, score, label


def _evaluate_pending_predictions(db: sqlite3.Connection):
    try:
        rows = db.execute(
            """
            SELECT *
            FROM prediction_records
            WHERE actual_outcome IS NULL
            ORDER BY predicted_on ASC
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return

    for row in rows:
        evaluation = _evaluate_record(db, row)
        if evaluation is None:
            continue
        actual_outcome, actual_risk, score, label = evaluation
        db.execute(
            """
            UPDATE prediction_records
            SET actual_outcome = ?, actual_risk = ?, accuracy_score = ?,
                accuracy_label = ?, evaluated_at = ?
            WHERE id = ?
            """,
            (
                actual_outcome,
                actual_risk,
                score,
                label,
                datetime.now().isoformat(),
                row["id"],
            ),
        )


def evaluate_prediction_accuracy(db: sqlite3.Connection) -> dict:
    _evaluate_pending_predictions(db)
    try:
        rows = db.execute(
            """
            SELECT *
            FROM prediction_records
            WHERE accuracy_score IS NOT NULL
            ORDER BY evaluated_at DESC, predicted_on DESC
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return {"status": "Prediction history unavailable"}

    if not rows:
        return {"status": "No evaluated predictions yet", "predictors": {}, "recent_evaluations": []}

    predictors = {}
    recent = []
    for row in rows:
        predictor = row["predictor_type"]
        meta = predictors.setdefault(
            predictor,
            {"total_evaluated": 0, "correct_count": 0, "score_total": 0.0, "recent_trend": []},
        )
        meta["total_evaluated"] += 1
        meta["score_total"] += float(row["accuracy_score"])
        if float(row["accuracy_score"]) >= 1.0:
            meta["correct_count"] += 1
        if len(meta["recent_trend"]) < 6:
            meta["recent_trend"].append(float(row["accuracy_score"]))
        if len(recent) < 10:
            recent.append(
                {
                    "predictor_type": predictor,
                    "target": row["target_label"],
                    "predicted_risk": row["predicted_risk"],
                    "actual_risk": row["actual_risk"],
                    "actual_outcome": row["actual_outcome"],
                    "accuracy_label": row["accuracy_label"],
                    "accuracy_score": round(float(row["accuracy_score"]), 2),
                    "predicted_on": row["predicted_on"],
                }
            )

    for predictor, meta in predictors.items():
        total = meta["total_evaluated"]
        meta["accuracy_pct"] = round((meta["score_total"] / total) * 100, 1) if total else 0
        del meta["score_total"]

    return {
        "status": "ok",
        "total_evaluated": len(rows),
        "predictors": predictors,
        "recent_evaluations": recent,
    }
