from sqlalchemy import Column, Integer, String, DateTime, ARRAY, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.database import Base

class DiaryEntry(Base):
    """Model for diary entries."""
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="diary_entries")
    
    def __repr__(self):
        return f"<DiaryEntry(id={self.id}, user_id={self.user_id}, mood={self.mood})>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "mood": self.mood,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 