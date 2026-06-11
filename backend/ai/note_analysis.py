import sqlite3
import re
from typing import List, Dict, Any, Optional
from .schemas import NoteAnalysisResult, NotePattern

CATEGORIES = {
    "Fatigue": ["tired", "sleep", "exhausted", "drowsy", "lazy", "fatigue", "nap", "rest", "sluggish"],
    "Stress": ["stress", "anxious", "pressure", "burn", "overwhelm", "panic", "nervous", "worry", "tense"],
    "Deep Work": ["focus", "deep work", "flow", "uninterrupted", "zone", "intense", "concentrate", "productive", "productivity"],
    "Distraction": ["distracted", "phone", "browsing", "social media", "noise", "interrupted", "delay", "procrastinate", "waste time"],
    "Motivation": ["motivated", "inspired", "excited", "low energy", "no energy", "lazy", "determined", "eager", "pumped"],
    "Progress": ["completed", "milestone", "finished", "done", "success", "built", "debugged", "ship", "launch"],
    "External Factors": ["weather", "family", "meeting", "work call", "call", "power cut", "transit", "travel", "rain", "sick", "headache"]
}

def analyze_notes(db: sqlite3.Connection, period_start: Optional[str] = None, period_end: Optional[str] = None) -> NoteAnalysisResult:
    # 1. Fetch notes from database
    query = """
        SELECT de.date, de.note, t.title as task_title 
        FROM daily_entries de 
        JOIN tasks t ON de.task_id = t.id 
        WHERE de.note IS NOT NULL AND de.note != ''
    """
    params = []
    
    if period_start and period_end:
        query += " AND de.date >= ? AND de.date <= ?"
        params.extend([period_start, period_end])
    elif period_start:
        query += " AND de.date >= ?"
        params.append(period_start)
    elif period_end:
        query += " AND de.date <= ?"
        params.append(period_end)
        
    query += " ORDER BY de.date DESC"
    
    rows = db.execute(query, params).fetchall()
    notes_list = [dict(row) for row in rows]
    
    total_notes = len(notes_list)
    
    # Initialize categorization mapping
    patterns: Dict[str, NotePattern] = {}
    for cat in CATEGORIES.keys():
        patterns[cat] = NotePattern(category=cat, count=0, percentage=0.0, matching_entries=[])
        
    # Analyze each note
    for entry in notes_list:
        note_text = entry["note"].lower()
        matched_categories = []
        
        for cat, keywords in CATEGORIES.items():
            found = False
            for kw in keywords:
                # Use word-boundary regex matching to prevent sub-string false positives
                if re.search(r'\b' + re.escape(kw) + r'\b', note_text):
                    found = True
                    break
            
            if found:
                patterns[cat].count += 1
                patterns[cat].matching_entries.append({
                    "date": entry["date"],
                    "task_title": entry["task_title"],
                    "note": entry["note"]
                })
                matched_categories.append(cat)
                
    # Calculate percentages and sort
    for cat in CATEGORIES.keys():
        if total_notes > 0:
            patterns[cat].percentage = round((patterns[cat].count / total_notes) * 100, 1)
            
    # Find dominant themes (categories that matched at least once, sorted by highest frequency)
    themes_with_count = [(cat, pattern.count) for cat, pattern in patterns.items() if pattern.count > 0]
    themes_with_count.sort(key=lambda x: x[1], reverse=True)
    dominant_themes = [cat for cat, _ in themes_with_count]
    
    return NoteAnalysisResult(
        total_notes_analyzed=total_notes,
        categories=patterns,
        dominant_themes=dominant_themes
    )
