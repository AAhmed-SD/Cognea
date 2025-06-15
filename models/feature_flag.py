from sqlalchemy import Column, String, Boolean, Integer, DateTime, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from models.database import Base

class FeatureFlagSetting(Base):
    """Model for managing feature flag settings and rollouts."""
    __tablename__ = "feature_flag_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    feature_name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    is_globally_enabled = Column(Boolean, default=False, nullable=False)
    rollout_percentage = Column(Integer, default=0, nullable=False)
    target_user_types = Column(ARRAY(String), default=[], nullable=False)
    conditions = Column(JSON, default=dict, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def is_active(self) -> bool:
        """Check if the feature flag is currently active based on dates."""
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def is_available_for_user(self, user_id: str, user_type: str) -> bool:
        """Check if the feature is available for a specific user."""
        if not self.is_globally_enabled or not self.is_active():
            return False

        # Check user type
        if self.target_user_types and user_type not in self.target_user_types:
            return False

        # Check rollout percentage
        if self.rollout_percentage < 100:
            user_hash = hash(str(user_id)) % 100
            return user_hash < self.rollout_percentage

        return True 