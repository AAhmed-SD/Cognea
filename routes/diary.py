from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/diary", tags=["Diary / Journal"])

class DiaryEntry(BaseModel):
    id: int
    user_id: int
    text: str
    mood: Optional[str]
    tags: Optional[List[str]]
    date: str

class DiaryEntryCreate(BaseModel):
    user_id: int
    text: str
    mood: Optional[str]
    tags: Optional[List[str]]
    date: str

@router.post("/entry", response_model=DiaryEntry, summary="Create a new diary/journal entry")
async def create_diary_entry(entry: DiaryEntryCreate):
    return DiaryEntry(id=1, **entry.dict())

@router.get("/entries/{user_id}", response_model=List[DiaryEntry], summary="List all diary entries for a user")
async def list_diary_entries(user_id: int):
    return [DiaryEntry(id=1, user_id=user_id, text="Sample entry", mood="happy", tags=["sample"], date="2024-06-01")]

@router.get("/entry/{entry_id}", response_model=DiaryEntry, summary="Retrieve a single diary entry")
async def get_diary_entry(entry_id: int):
    return DiaryEntry(id=entry_id, user_id=1, text="Sample entry", mood="happy", tags=["sample"], date="2024-06-01")

@router.put("/entry/{entry_id}", response_model=DiaryEntry, summary="Update a diary entry")
async def update_diary_entry(entry_id: int, entry: DiaryEntryCreate):
    return DiaryEntry(id=entry_id, **entry.dict())

@router.delete("/entry/{entry_id}", summary="Delete a diary entry")
async def delete_diary_entry(entry_id: int):
    return {"message": f"Diary entry {entry_id} deleted"}

@router.get("/stats/{user_id}", summary="Get mood/sentiment trends over diary entries")
async def diary_stats(user_id: int):
    return {"user_id": user_id, "trend": "happy"}

@router.post("/entry/reflect", summary="AI-generated reflection prompt based on past week")
async def diary_reflect():
    return {"prompt": "What was the highlight of your week?"}

@router.post("/diary-entry", summary="Create a new diary/journal entry (checklist)")
async def create_diary_entry_checklist():
    return {"message": "Created diary entry (checklist)"}

@router.get("/diary-entries/{user_id}", summary="List all diary entries for a user (checklist)")
async def list_diary_entries_checklist(user_id: int):
    return {"entries": []}

@router.get("/diary-entry/{entry_id}", summary="Retrieve a single diary entry (checklist)")
async def get_diary_entry_checklist(entry_id: int):
    return {"entry": {"id": entry_id}}

@router.put("/diary-entry/{entry_id}", summary="Update a diary entry (checklist)")
async def update_diary_entry_checklist(entry_id: int):
    return {"message": f"Updated diary entry {entry_id} (checklist)"}

@router.delete("/diary-entry/{entry_id}", summary="Delete a diary entry (checklist)")
async def delete_diary_entry_checklist(entry_id: int):
    return {"message": f"Deleted diary entry {entry_id} (checklist)"}

@router.get("/diary-stats/{user_id}", summary="Get mood/sentiment trends over diary entries (checklist)")
async def diary_stats_checklist(user_id: int):
    return {"user_id": user_id, "trend": "happy"}

@router.post("/diary-entry/reflect", summary="AI-generated reflection prompt based on past week (checklist)")
async def diary_reflect_checklist():
    return {"prompt": "What was the highlight of your week? (checklist)"} 