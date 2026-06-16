from pydantic import BaseModel, Field
from typing import Optional

class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    category: str = Field(..., description="Long-Term Goals, Short-Term Goals, or Step-Up Goals")
    target_date: Optional[str] = None
    progress: Optional[int] = 0
    priority: Optional[int] = 0

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    progress: Optional[int] = None
    priority: Optional[int] = None
    target_date: Optional[str] = None
    completed: Optional[int] = None

