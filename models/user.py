from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)

    audit_logs = relationship("AuditLog", back_populates="user")
    plans = relationship("Plan", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")
    flashcard_reviews = relationship("FlashcardReview", back_populates="user") 