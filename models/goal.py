"""
Goal model for the Personal Agent application.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    due_date: datetime | None = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    is_starred: bool = False


class GoalCreate(GoalBase):
    user_id: UUID


class GoalUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    due_date: datetime | None = None
    priority: PriorityLevel | None = None
    status: str | None = None
    progress: int | None = Field(None, ge=0, le=100)
    is_starred: bool | None = None
    analytics: dict[str, Any] | None = None


class Goal(GoalBase):
    id: UUID
    user_id: UUID
    status: str = "Not Started"
    progress: int = 0
    analytics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
