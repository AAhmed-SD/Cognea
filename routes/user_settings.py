from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.audit import AuditAction, log_audit_from_request
from services.supabase import get_supabase_client

router = APIRouter(prefix="/user/settings", tags=["User Settings"])


class UserSettings(BaseModel):
    user_id: int
    focus_hours: str | None
    energy_curve: str | None
    enabled_modules: str | None
    default_views: str | None


@router.get("/", response_model=UserSettings, summary="Retrieve all preferences")
async def get_user_settings(user_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(user_id),
        action=AuditAction.READ,
        resource="user_settings",
    )

    supabase = get_supabase_client()
    result = (
        supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="User settings not found")

    settings_data = result.data[0]
    return UserSettings(**settings_data)


@router.post(
    "/",
    response_model=UserSettings,
    summary="Update focus hours, energy curve, enabled modules, default views",
)
async def update_user_settings(settings: UserSettings, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(settings.user_id),
        action=AuditAction.UPDATE,
        resource="user_settings",
        details={"payload": settings.dict()},
    )

    supabase = get_supabase_client()

    # Check if settings exist for this user
    existing_result = (
        supabase.table("user_settings")
        .select("*")
        .eq("user_id", settings.user_id)
        .execute()
    )

    if existing_result.data:
        # Update existing settings
        result = (
            supabase.table("user_settings")
            .update(settings.dict())
            .eq("user_id", settings.user_id)
            .execute()
        )
    else:
        # Create new settings
        result = supabase.table("user_settings").insert(settings.dict()).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update user settings")

    return UserSettings(**result.data[0])


@router.get("/features", summary="Get toggles: flashcards, habits, etc.")
async def get_feature_toggles(user_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(user_id),
        action=AuditAction.READ,
        resource="user_features",
    )

    supabase = get_supabase_client()
    result = (
        supabase.table("user_features").select("*").eq("user_id", user_id).execute()
    )

    if result.data:
        features = result.data[0].get(
            "features", ["flashcards", "habits", "calendar", "notion"]
        )
    else:
        # Default features if none found
        features = ["flashcards", "habits", "calendar", "notion"]

    return {"user_id": user_id, "features": features}
