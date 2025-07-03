"""
Flashcard model for the Personal Agent application.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FlashcardBase(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    tags: list[str] | None = Field(default_factory=list)
    deck_id: UUID | None = None
    deck_name: str | None = None


class FlashcardCreate(FlashcardBase):
    user_id: UUID


class FlashcardUpdate(BaseModel):
    question: str | None = Field(None, min_length=1)
    answer: str | None = Field(None, min_length=1)
    tags: list[str] | None = None
    deck_id: UUID | None = None
    deck_name: str | None = None
    last_reviewed_at: datetime | None = None
    next_review_date: datetime | None = None
    ease_factor: float | None = None
    interval: int | None = None


class Flashcard(FlashcardBase):
    id: UUID
    user_id: UUID
    last_reviewed_at: datetime | None = None
    next_review_date: datetime | None = None
    ease_factor: float = 2.5
    interval: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
