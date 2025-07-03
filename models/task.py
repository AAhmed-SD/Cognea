"""
Task model for the Personal Agent application.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    due_date: datetime | None = None
    priority: PriorityLevel = PriorityLevel.MEDIUM


class TaskCreate(TaskBase):
    user_id: UUID


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    priority: PriorityLevel | None = None


class Task(TaskBase):
    id: UUID
    user_id: UUID
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
