from fastapi import APIRouter

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Management"])

# In-memory user_data_db removed. Add real database queries for user data export/delete here.


@router.post("/export-data/{user_id}", summary="Export all data (GDPR, CSV or JSON)")
async def export_data(user_id: int):
    # Simulate export as JSON
    return {"user_id": user_id, "export": {"habits": [], "moods": [], "diary": []}}


@router.delete("/delete-account/{user_id}", summary="Delete account + anonymize data")
async def delete_account(user_id: int):
    return {"user_id": user_id, "status": "not found"}


@router.get("/summary", summary="Show user what data is stored")
async def privacy_summary():
    # Simulate a summary of stored data
    return {
        "summary": "We store your habits, moods, diary entries, and profile data for your account."
    }
