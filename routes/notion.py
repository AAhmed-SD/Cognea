from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/notion", tags=["Notion Sync"])

# In-memory storage for Notion connections and tasks
notion_connections_db: Dict[int, dict] = {}
notion_tasks_db: Dict[int, List[dict]] = {}

class NotionPushTasksRequest(BaseModel):
    user_id: int
    tasks: List[str]

class NotionWebhookRequest(BaseModel):
    user_id: int
    event: dict

@router.post("/connect", summary="Start Notion API integration")
async def notion_connect(user_id: int):
    notion_connections_db[user_id] = {"connected": True, "connected_at": datetime.now().isoformat()}
    return {"user_id": user_id, "status": "notion connected", "connected_at": notion_connections_db[user_id]["connected_at"]}

@router.get("/pull-tasks", summary="Import tasks or notes from Notion")
async def notion_pull_tasks(user_id: int):
    tasks = notion_tasks_db.get(user_id, [
        {"id": 1, "title": "Sample Notion Task", "created": datetime.now().isoformat()}
    ])
    return {"user_id": user_id, "tasks": tasks}

@router.post("/push-tasks", summary="Push tasks or flashcards to Notion")
async def notion_push_tasks(request: NotionPushTasksRequest):
    # Simulate pushing tasks to Notion
    user_tasks = notion_tasks_db.setdefault(request.user_id, [])
    for task in request.tasks:
        user_tasks.append({"id": len(user_tasks)+1, "title": task, "created": datetime.now().isoformat()})
    return {"user_id": request.user_id, "status": "tasks pushed to Notion", "tasks": user_tasks}

@router.post("/webhook-handler", summary="Handle updates from Notion in real time")
async def notion_webhook_handler(request: NotionWebhookRequest):
    # Simulate webhook event handling
    return {"user_id": request.user_id, "status": "webhook received", "event": request.event} 