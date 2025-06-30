from datetime import datetime
from typing import List, Optional, Dict, Any
from models.feature_flag import FeatureFlagSetting
from models.database import db


class FeatureFlagService:
    @staticmethod
    def create_feature_flag(
        feature_name: str,
        description: Optional[str] = None,
        is_globally_enabled: bool = False,
        rollout_percentage: int = 0,
        target_user_types: List[str] = None,
        conditions: Dict[str, Any] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FeatureFlagSetting:
        """Create a new feature flag setting."""
        feature_flag = FeatureFlagSetting(
            feature_name=feature_name,
            description=description,
            is_globally_enabled=is_globally_enabled,
            rollout_percentage=rollout_percentage,
            target_user_types=target_user_types or [],
            conditions=conditions or {},
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(feature_flag)
        db.session.commit()
        return feature_flag

    @staticmethod
    def get_feature_flag(feature_name: str) -> Optional[FeatureFlagSetting]:
        """Get a feature flag setting by name."""
        return FeatureFlagSetting.query.filter_by(feature_name=feature_name).first()

    @staticmethod
    def update_feature_flag(
        feature_name: str, **kwargs
    ) -> Optional[FeatureFlagSetting]:
        """Update a feature flag setting."""
        feature_flag = FeatureFlagService.get_feature_flag(feature_name)
        if not feature_flag:
            return None

        for key, value in kwargs.items():
            if hasattr(feature_flag, key):
                setattr(feature_flag, key, value)

        db.session.commit()
        return feature_flag

    @staticmethod
    def delete_feature_flag(feature_name: str) -> bool:
        """Delete a feature flag setting."""
        feature_flag = FeatureFlagService.get_feature_flag(feature_name)
        if not feature_flag:
            return False

        db.session.delete(feature_flag)
        db.session.commit()
        return True

    @staticmethod
    def list_feature_flags(
        is_globally_enabled: Optional[bool] = None,
        target_user_type: Optional[str] = None,
    ) -> List[FeatureFlagSetting]:
        """List feature flags with optional filtering."""
        query = FeatureFlagSetting.query

        if is_globally_enabled is not None:
            query = query.filter_by(is_globally_enabled=is_globally_enabled)

        if target_user_type:
            query = query.filter(
                FeatureFlagSetting.target_user_types.contains([target_user_type])
            )

        return query.all()

    @staticmethod
    def is_feature_enabled_for_user(
        user_id: str, user_type: str, feature_name: str
    ) -> bool:
        """Check if a feature is enabled for a specific user."""
        feature_flag = FeatureFlagService.get_feature_flag(feature_name)
        if not feature_flag:
            return False

        return feature_flag.is_available_for_user(user_id, user_type)
