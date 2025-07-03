"""
Notification model for the Personal Agent application.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationType(str, Enum):
    REMINDER = "reminder"
    ALERT = "alert"
    SYSTEM = "system"


class NotificationCategory(str, Enum):
    TASK = "task"
    GOAL = "goal"
    SYSTEM = "system"
    ALERT = "alert"


class RepeatInterval(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    send_time: datetime
    type: NotificationType = NotificationType.REMINDER
    category: NotificationCategory = NotificationCategory.TASK
    repeat_interval: RepeatInterval | None = None


class NotificationCreate(NotificationBase):
    user_id: UUID


class NotificationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    message: str | None = Field(None, min_length=1)
    send_time: datetime | None = None
    type: NotificationType | None = None
    category: NotificationCategory | None = None
    is_sent: bool | None = None
    is_read: bool | None = None
    repeat_interval: RepeatInterval | None = None


class Notification(NotificationBase):
    id: UUID
    user_id: UUID
    is_sent: bool = False
    is_read: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
