from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Management"])

# In-memory storage for user data (simulate export/delete)
user_data_db: Dict[int, dict] = {}


@router.post("/export-data/{user_id}", summary="Export all data (GDPR, CSV or JSON)")
async def export_data(user_id: int):
    data = user_data_db.get(user_id, {"habits": [], "moods": [], "diary": []})
    # Simulate export as JSON
    return {"user_id": user_id, "export": data}


@router.delete("/delete-account/{user_id}", summary="Delete account + anonymize data")
async def delete_account(user_id: int):
    if user_id in user_data_db:
        user_data_db[user_id] = {"anonymized": True}
        return {"user_id": user_id, "status": "deleted and anonymized"}
    return {"user_id": user_id, "status": "not found"}


@router.get("/summary", summary="Show user what data is stored")
async def privacy_summary():
    # Simulate a summary of stored data
    return {
        "summary": "We store your habits, moods, diary entries, and profile data for your account."
    }
