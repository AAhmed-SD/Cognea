"""
Notification model for the Personal Agent application.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

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
    repeat_interval: Optional[RepeatInterval] = None

class NotificationCreate(NotificationBase):
    user_id: UUID

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    send_time: Optional[datetime] = None
    type: Optional[NotificationType] = None
    category: Optional[NotificationCategory] = None
    is_sent: Optional[bool] = None
    is_read: Optional[bool] = None
    repeat_interval: Optional[RepeatInterval] = None

class Notification(NotificationBase):
    id: UUID
    user_id: UUID
    is_sent: bool = False
    is_read: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 