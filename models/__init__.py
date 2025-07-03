"""
Database models for the Personal Agent application.
"""

from .flashcard import Flashcard
from .goal import Goal
from .notification import Notification
from .schedule_block import ScheduleBlock
from .task import Task
from .user import User

__all__ = ["User", "Task", "Goal", "ScheduleBlock", "Flashcard", "Notification"]

# Models package initialization
# All SQLAlchemy models have been removed in favor of Supabase
# Only Pydantic models remain for request/response validation
