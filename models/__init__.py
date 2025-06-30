"""
Database models for the Personal Agent application.
"""

from .user import User
from .task import Task
from .goal import Goal
from .schedule_block import ScheduleBlock
from .flashcard import Flashcard
from .notification import Notification

__all__ = [
    "User",
    "Task", 
    "Goal",
    "ScheduleBlock",
    "Flashcard",
    "Notification"
]

# Models package initialization 
# All SQLAlchemy models have been removed in favor of Supabase
# Only Pydantic models remain for request/response validation 