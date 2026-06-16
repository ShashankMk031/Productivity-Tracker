from pydantic import BaseModel, Field
from typing import Dict, Optional, List



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


