from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/user-profile", tags=["Adaptive Profile & Preferences"])


class UserProfile(BaseModel):
    user_id: int
    focus_hours: str | None
    energy_curve: str | None
    goal_weightings: str | None


# In-memory storage for user profiles
user_profiles_db: dict[int, UserProfile] = {}


@router.put(
    "/{user_id}",
    response_model=UserProfile,
    summary="Update focus hours, energy curve, goal weightings",
)
async def update_user_profile(user_id: int, profile: UserProfile):
    pass
    user_profiles_db[user_id] = profile
    return profile


@router.get(
    "/{user_id}", response_model=UserProfile, summary="Retrieve full adaptive profile"
)
async def get_user_profile(user_id: int):
    pass
    profile = user_profiles_db.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile
