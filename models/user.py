import uuid
from sqlalchemy import Column, String, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base
from models.feature_flag import FeatureFlagSetting

class User(Base):
    """User model with feature flags and audit fields."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    feature_flags = Column(JSON, default=dict, nullable=False)
    user_type = Column(String, default="student", nullable=False)
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
        # First check user-specific flag
        if feature_name in self.feature_flags:
            return self.feature_flags[feature_name]
        
        # Then check global settings
        feature_setting = FeatureFlagSetting.query.filter_by(
            feature_name=feature_name,
            is_globally_enabled=True
        ).first()
        
        if not feature_setting:
            return False
            
        return feature_setting.is_available_for_user(str(self.id), self.user_type)

    def enable_feature(self, feature_name: str):
        """Enable a feature for this specific user."""
        self.feature_flags[feature_name] = True

    def disable_feature(self, feature_name: str):
        """Disable a feature for this specific user."""
        self.feature_flags[feature_name] = False 