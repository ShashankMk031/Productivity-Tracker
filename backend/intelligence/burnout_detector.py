import sqlite3
from datetime import datetime, timedelta

def detect_burnout(db: sqlite3.Connection) -> dict:
    now = datetime.now()
    
    # 1. Analyze Fatigue Notes
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()
    
    # Negative keywords
    fatigue_keywords = ['tired', 'exhausted', 'burnout', 'fatigue', 'drained', 'overwhelmed', 'stress', 'cant focus']
    
    # Get daily entries in last 30 days
    recent_entries = db.execute(
        "SELECT date, note FROM daily_entries WHERE date >= ? AND note != ''", 
        ((now - timedelta(days=30)).strftime("%Y-%m-%d"),)
    ).fetchall()
    
    recent_sessions = db.execute(
        "SELECT start_time, notes FROM focus_sessions WHERE start_time >= ? AND notes != ''",
        (thirty_days_ago,)
    ).fetchall()
    total_text_samples = len(recent_entries) + len(recent_sessions)

    def count_fatigue(texts):
        count = 0
        for text in texts:
            if not text: continue
            text_lower = text.lower()
            if any(k in text_lower for k in fatigue_keywords):
                count += 1
        return count
        
    # Split into last 14 days vs previous 14 days
    last_14_texts = []
    prev_14_texts = []
    
    for row in recent_entries:
        if row["date"] >= (now - timedelta(days=14)).strftime("%Y-%m-%d"):
            last_14_texts.append(row["note"])
        else:
            prev_14_texts.append(row["note"])
            
    for row in recent_sessions:
        if row["start_time"] >= fourteen_days_ago:
            last_14_texts.append(row["notes"])
        else:
            prev_14_texts.append(row["notes"])

    fatigue_last_14 = count_fatigue(last_14_texts)
    fatigue_prev_14 = count_fatigue(prev_14_texts)
    
    # 2. Focus Session Decline
    focus_last_14 = db.execute("SELECT COUNT(*) as c, SUM(duration) as d FROM focus_sessions WHERE start_time >= ?", (fourteen_days_ago,)).fetchone()
    focus_prev_14 = db.execute("SELECT COUNT(*) as c, SUM(duration) as d FROM focus_sessions WHERE start_time >= ? AND start_time < ?", (thirty_days_ago, fourteen_days_ago)).fetchone()
    
    d_last_14 = focus_last_14["d"] or 0
    d_prev_14 = focus_prev_14["d"] or 0
    
    focus_drop_pct = 0
    if d_prev_14 > 0:
        focus_drop_pct = ((d_prev_14 - d_last_14) / d_prev_14) * 100
        
    # 3. Missed tasks recently
    miss_last_14 = db.execute("SELECT COUNT(*) as c FROM daily_entries WHERE completed=0 AND date >= ?", ((now - timedelta(days=14)).strftime("%Y-%m-%d"),)).fetchone()["c"]
    miss_prev_14 = db.execute("SELECT COUNT(*) as c FROM daily_entries WHERE completed=0 AND date >= ? AND date < ?", ((now - timedelta(days=30)).strftime("%Y-%m-%d"), (now - timedelta(days=14)).strftime("%Y-%m-%d"))).fetchone()["c"]

    # Compile Risk
    score = 0
    reasons = []
    
    if fatigue_last_14 > fatigue_prev_14 and fatigue_last_14 > 2:
        score += 40
        reasons.append(f"Fatigue mentions increased ({fatigue_prev_14} → {fatigue_last_14})")
    elif fatigue_last_14 > 0:
        score += 20
        reasons.append(f"Recent fatigue mentions detected ({fatigue_last_14})")
        
    if focus_drop_pct > 30:
        score += 30
        reasons.append(f"Focus duration dropped by {int(focus_drop_pct)}%")
        
    if miss_last_14 > miss_prev_14 and miss_last_14 > 5:
        score += 30
        reasons.append(f"Missed tasks increased ({miss_prev_14} → {miss_last_14})")
        
    if score >= 70:
        risk = "HIGH"
        warning = "CRITICAL"
        confidence = 85
    elif score >= 40:
        risk = "MEDIUM"
        warning = "WARNING"
        confidence = 75
    elif score >= 20:
        risk = "LOW"
        warning = "WATCH"
        confidence = 65
    else:
        risk = "LOW"
        warning = "INFO"
        confidence = 90
        reasons.append("No significant fatigue or productivity drop detected")

    return {
        "risk_level": risk,
        "warning_level": warning,
        "reason": " and ".join(reasons) if reasons else "Stable performance patterns",
        "supporting_metrics": {
            "fatigue_mentions_last_14d": fatigue_last_14,
            "fatigue_mentions_prev_14d": fatigue_prev_14,
            "focus_duration_drop_pct": int(focus_drop_pct) if focus_drop_pct > 0 else 0,
            "missed_tasks_last_14d": miss_last_14,
            "missed_tasks_prev_14d": miss_prev_14,
            "sample_size": total_text_samples + (focus_last_14["c"] or 0) + (focus_prev_14["c"] or 0),
            "data_completeness": round(min(total_text_samples / 12, 1), 2),
        },
        "confidence": confidence
    }
