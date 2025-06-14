from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

router = APIRouter(prefix="/user/settings", tags=["User Settings"])

class UserSettings(BaseModel):
    user_id: int
    focus_hours: Optional[str]
    energy_curve: Optional[str]
    enabled_modules: Optional[str]
    default_views: Optional[str]

# In-memory storage for user settings
user_settings_db: Dict[int, UserSettings] = {}
user_features_db: Dict[int, List[str]] = {}

@router.get("/", response_model=UserSettings, summary="Retrieve all preferences")
async def get_user_settings(user_id: int):
    settings = user_settings_db.get(user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="User settings not found")
    return settings

@router.post("/", response_model=UserSettings, summary="Update focus hours, energy curve, enabled modules, default views")
async def update_user_settings(settings: UserSettings):
    user_settings_db[settings.user_id] = settings
    return settings

@router.get("/features", summary="Get toggles: flashcards, habits, etc.")
async def get_feature_toggles(user_id: int):
    features = user_features_db.get(user_id, ["flashcards", "habits", "calendar", "notion"])
    return {"user_id": user_id, "features": features} 