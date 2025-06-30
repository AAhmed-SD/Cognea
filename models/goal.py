"""
Goal model for the Personal Agent application.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import ConfigDict


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    is_starred: bool = False


class GoalCreate(GoalBase):
    user_id: UUID


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[PriorityLevel] = None
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    is_starred: Optional[bool] = None
    analytics: Optional[Dict[str, Any]] = None


class Goal(GoalBase):
    id: UUID
    user_id: UUID
    status: str = "Not Started"
    progress: int = 0
    analytics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
