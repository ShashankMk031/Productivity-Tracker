from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NotePattern(BaseModel):
    category: str
    count: int = 0
    percentage: float = 0.0
    matching_entries: List[Dict[str, Any]] = Field(default_factory=list)

class NoteAnalysisResult(BaseModel):
    total_notes_analyzed: int
    categories: Dict[str, NotePattern]
    dominant_themes: List[str] = Field(default_factory=list)

class BehavioralSummary(BaseModel):
    completion_rate: float
    current_streak: int
    longest_streak: int
    productive_weekdays: List[str] = Field(default_factory=list)
    weak_weekdays: List[str] = Field(default_factory=list)
    missed_days_count: int
    active_tasks_count: int

class GoalProgressInfo(BaseModel):
    id: int
    title: str
    category: str
    progress: int
    target_date: Optional[str] = None
    completed: int

class ProjectMilestoneInfo(BaseModel):
    id: int
    title: str
    completed: int

class ProjectProgressInfo(BaseModel):
    id: int
    title: str
    deadline: str
    progress: int
    urgency: str
    milestones: List[ProjectMilestoneInfo] = Field(default_factory=list)

class AIContextPackage(BaseModel):
    analytics: Dict[str, Any]
    notes: NoteAnalysisResult
    goals: List[GoalProgressInfo] = Field(default_factory=list)
    projects: List[ProjectProgressInfo] = Field(default_factory=list)
    behavioral_patterns: BehavioralSummary
    generated_at: str
    period_type: str  # 'weekly' or 'monthly'
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    focus_stats: Optional[Dict[str, Any]] = None
    reminder_stats: Optional[Dict[str, Any]] = None
    scores: Optional[Dict[str, Any]] = None
    intelligence_snapshot: Optional[Dict[str, Any]] = None
    prediction_accuracy: Optional[Dict[str, Any]] = None
    prediction_summary_markdown: Optional[str] = None
