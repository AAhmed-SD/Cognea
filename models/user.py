import uuid
from sqlalchemy import Column, String, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class User(Base):
    """User model with feature flags and audit fields."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    feature_flags = Column(JSON, default=dict, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    diary_entries = relationship(
        "DiaryEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def has_feature(self, feature_name: str) -> bool:
        """Check if a feature flag is enabled for this user."""
        return self.feature_flags.get(feature_name, False)

    def enable_feature(self, feature_name: str):
        self.feature_flags[feature_name] = True

    def disable_feature(self, feature_name: str):
        self.feature_flags[feature_name] = False 