"""
Flashcard model for the Personal Agent application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict


class FlashcardBase(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    tags: Optional[List[str]] = Field(default_factory=list)
    deck_id: Optional[UUID] = None
    deck_name: Optional[str] = None


class FlashcardCreate(FlashcardBase):
    user_id: UUID


class FlashcardUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    deck_id: Optional[UUID] = None
    deck_name: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    ease_factor: Optional[float] = None
    interval: Optional[int] = None


class Flashcard(FlashcardBase):
    id: UUID
    user_id: UUID
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    ease_factor: float = 2.5
    interval: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
