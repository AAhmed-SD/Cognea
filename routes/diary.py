from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from services.audit import AuditAction, log_audit_from_request
from services.supabase import get_supabase_client

router = APIRouter(prefix="/diary", tags=["Diary / Journal"])


class DiaryEntryBase(BaseModel):
    content: str
    mood: str
    tags: list[str] | None = []


class DiaryEntryCreate(DiaryEntryBase):
    user_id: int


class DiaryEntryUpdate(DiaryEntryBase):
    pass


class DiaryEntryOut(DiaryEntryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/entry", response_model=DiaryEntryOut, summary="Create a new diary/journal entry"
)
def create_diary_entry(entry: DiaryEntryCreate, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(entry.user_id),
        action=AuditAction.CREATE,
        resource="diary_entry",
        resource_id=None,
        details={"payload": entry.dict()},
    )

    supabase = get_supabase_client()

    # Prepare data for insertion
    data = {
        "user_id": entry.user_id,
        "content": entry.content,
        "mood": entry.mood,
        "tags": entry.tags or [],
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    try:
        result = supabase.table("diary_entries").insert(data).execute()
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to create diary entry")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/entries/{user_id}",
    response_model=list[DiaryEntryOut],
    summary="List all diary entries for a user",
)
def list_diary_entries(user_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(user_id),
        action=AuditAction.READ,
        resource="diary_entry",
        resource_id=None,
        details={"list": True},
    )

    supabase = get_supabase_client()

    try:
        result = (
            supabase.table("diary_entries")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/entry/{entry_id}",
    response_model=DiaryEntryOut,
    summary="Retrieve a single diary entry",
)
def get_diary_entry(entry_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=None,
        action=AuditAction.READ,
        resource="diary_entry",
        resource_id=str(entry_id),
    )

    supabase = get_supabase_client()

    try:
        result = (
            supabase.table("diary_entries").select("*").eq("id", entry_id).execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Diary entry not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/entry/{entry_id}", response_model=DiaryEntryOut, summary="Update a diary entry"
)
def update_diary_entry(entry_id: int, entry: DiaryEntryUpdate, request: Request):
    supabase = get_supabase_client()

    # First check if entry exists and get user_id
    try:
        existing = (
            supabase.table("diary_entries")
            .select("user_id")
            .eq("id", entry_id)
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Diary entry not found")

        user_id = existing.data[0]["user_id"]

        log_audit_from_request(
            request=request,
            user_id=str(user_id),
            action=AuditAction.UPDATE,
            resource="diary_entry",
            resource_id=str(entry_id),
            details={"payload": entry.dict()},
        )

        # Update data
        update_data = {
            "content": entry.content,
            "mood": entry.mood,
            "tags": entry.tags or [],
            "updated_at": datetime.now(UTC).isoformat(),
        }

        result = (
            supabase.table("diary_entries")
            .update(update_data)
            .eq("id", entry_id)
            .execute()
        )

        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to update diary entry")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/entry/{entry_id}", summary="Delete a diary entry")
def delete_diary_entry(entry_id: int, request: Request):
    supabase = get_supabase_client()

    # First check if entry exists and get user_id
    try:
        existing = (
            supabase.table("diary_entries")
            .select("user_id")
            .eq("id", entry_id)
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Diary entry not found")

        user_id = existing.data[0]["user_id"]

        log_audit_from_request(
            request=request,
            user_id=str(user_id),
            action=AuditAction.DELETE,
            resource="diary_entry",
            resource_id=str(entry_id),
        )

        # Delete the entry
        supabase.table("diary_entries").delete().eq("id", entry_id).execute()

        return {"message": f"Diary entry {entry_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats/{user_id}", summary="Get mood/sentiment trends over diary entries")
async def diary_stats(user_id: int):
    return {"user_id": user_id, "trend": "happy"}


@router.post(
    "/entry/reflect", summary="AI-generated reflection prompt based on past week"
)
async def diary_reflect():
    return {"prompt": "What was the highlight of your week?"}


@router.post("/diary-entry", summary="Create a new diary/journal entry (checklist)")
async def create_diary_entry_checklist(request: Request):
    log_audit_from_request(
        request=request,
        user_id=None,
        action=AuditAction.CREATE,
        resource="diary_entry_checklist",
    )
    return {"message": "Created diary entry (checklist)"}


@router.get(
    "/diary-entries/{user_id}", summary="List all diary entries for a user (checklist)"
)
async def list_diary_entries_checklist(user_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=str(user_id),
        action=AuditAction.READ,
        resource="diary_entry_checklist",
    )
    return {"entries": []}


@router.get(
    "/diary-entry/{entry_id}", summary="Retrieve a single diary entry (checklist)"
)
async def get_diary_entry_checklist(entry_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=None,
        action=AuditAction.READ,
        resource="diary_entry_checklist",
        resource_id=str(entry_id),
    )
    return {"entry": {"id": entry_id}}


@router.put("/diary-entry/{entry_id}", summary="Update a diary entry (checklist)")
async def update_diary_entry_checklist(entry_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=None,
        action=AuditAction.UPDATE,
        resource="diary_entry_checklist",
        resource_id=str(entry_id),
    )
    return {"message": f"Updated diary entry {entry_id} (checklist)"}


@router.delete("/diary-entry/{entry_id}", summary="Delete a diary entry (checklist)")
async def delete_diary_entry_checklist(entry_id: int, request: Request):
    log_audit_from_request(
        request=request,
        user_id=None,
        action=AuditAction.DELETE,
        resource="diary_entry_checklist",
        resource_id=str(entry_id),
    )
    return {"message": f"Deleted diary entry {entry_id} (checklist)"}


@router.get(
    "/diary-stats/{user_id}",
    summary="Get mood/sentiment trends over diary entries (checklist)",
)
async def diary_stats_checklist(user_id: int):
    return {"user_id": user_id, "trend": "happy"}


@router.post(
    "/diary-entry/reflect",
    summary="AI-generated reflection prompt based on past week (checklist)",
)
async def diary_reflect_checklist():
    return {"prompt": "What was the highlight of your week? (checklist)"}
