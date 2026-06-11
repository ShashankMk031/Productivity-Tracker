from pydantic import BaseModel, Field
from typing import Dict, Optional, List

class DaysSchedule(BaseModel):
    Mon: bool = True
    Tue: bool = True
    Wed: bool = True
    Thu: bool = True
    Fri: bool = True
    Sat: bool = True
    Sun: bool = True

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    active_days: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1)
    active_days: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

class EntryToggle(BaseModel):
    task_id: int
    date: str

class NoteUpdate(BaseModel):
    task_id: int
    date: str
    note: str

# Reponse models
class TaskResponse(BaseModel):
    id: int
    title: str
    active_days: str
    is_archived: int
    created_at: str

class EntryResponse(BaseModel):
    id: int
    task_id: int
    date: str
    completed: int
    note: Optional[str] = None
