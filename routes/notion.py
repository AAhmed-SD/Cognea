from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from services.supabase import get_supabase_client
from services.auth import get_current_user
import httpx
import json
import os
from urllib.parse import urlencode

router = APIRouter(prefix="/api/notion", tags=["Notion Sync"])

# Notion API configuration
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "http://localhost:8000/api/notion/callback")

class NotionAuthRequest(BaseModel):
    code: str
    state: str

class NotionDatabaseRequest(BaseModel):
    database_id: str
    sync_type: str = "bidirectional"  # "pull", "push", "bidirectional"

class NotionTaskSync(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = []

class NotionWebhookRequest(BaseModel):
    type: str
    workspace_id: str
    page_id: Optional[str] = None
    database_id: Optional[str] = None

@router.get("/auth/url", summary="Get Notion OAuth URL")
async def get_notion_auth_url(current_user: dict = Depends(get_current_user)):
    if not NOTION_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Notion client ID not configured")
    state = f"user_{current_user['id']}_{datetime.now().timestamp()}"
    auth_params = {
        "client_id": NOTION_CLIENT_ID,
        "redirect_uri": NOTION_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "owner": "user"
    }
    auth_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(auth_params)}"
    return {"auth_url": auth_url, "state": state}

@router.post("/auth/callback", summary="Handle Notion OAuth callback")
async def notion_auth_callback(
    request: NotionAuthRequest,
    current_user: dict = Depends(get_current_user)
):
    if not NOTION_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Notion client secret not configured")
    token_data = {
        "grant_type": "authorization_code",
        "code": request.code,
        "redirect_uri": NOTION_REDIRECT_URI
    }
    headers = {
        "Authorization": f"Basic {NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/oauth/token",
            json=token_data,
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        token_info = response.json()
        # Store connection info in Supabase
        supabase = get_supabase_client()
        connection_data = {
            "user_id": current_user["id"],
            "access_token": token_info["access_token"],
            "workspace_id": token_info["workspace_id"],
            "workspace_name": token_info.get("workspace_name", ""),
            "connected_at": datetime.now().isoformat(),
            "bot_id": token_info.get("bot_id", "")
        }
        # Upsert connection
        existing = supabase.table("notion_connections").select("*").eq("user_id", current_user["id"]).execute()
        if existing.data:
            supabase.table("notion_connections").update(connection_data).eq("user_id", current_user["id"]).execute()
        else:
            supabase.table("notion_connections").insert(connection_data).execute()
        return {
            "success": True,
            "workspace_name": token_info.get("workspace_name", ""),
            "connected_at": datetime.now().isoformat()
        }

@router.get("/databases", summary="List user's Notion databases")
async def list_notion_databases(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    connection_result = supabase.table("notion_connections").select("*").eq("user_id", current_user["id"]).execute()
    if not connection_result.data:
        raise HTTPException(status_code=401, detail="Notion not connected")
    connection = connection_result.data[0]
    headers = {
        "Authorization": f"Bearer {connection['access_token']}",
        "Notion-Version": "2022-06-28"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/search",
            json={"filter": {"property": "object", "value": "database"}},
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch databases")
        databases = response.json().get("results", [])
        return {
            "success": True,
            "databases": [
                {
                    "id": db["id"],
                    "title": db["title"][0]["plain_text"] if db["title"] else "Untitled",
                    "created_time": db["created_time"],
                    "last_edited_time": db["last_edited_time"]
                }
                for db in databases
            ]
        }

@router.post("/sync/database", summary="Sync with a specific Notion database")
async def sync_notion_database(
    request: NotionDatabaseRequest,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    connection_result = supabase.table("notion_connections").select("*").eq("user_id", current_user["id"]).execute()
    if not connection_result.data:
        raise HTTPException(status_code=401, detail="Notion not connected")
    connection = connection_result.data[0]
    headers = {
        "Authorization": f"Bearer {connection['access_token']}",
        "Notion-Version": "2022-06-28"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/databases/{request.database_id}/query",
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to query database")
        database_content = response.json()
        pages = database_content.get("results", [])
        tasks = []
        for page in pages:
            properties = page.get("properties", {})
            title = "Untitled"
            for prop_name, prop_value in properties.items():
                if prop_value.get("type") == "title" and prop_value.get("title"):
                    title = prop_value["title"][0]["plain_text"]
                    break
            due_date = None
            priority = "medium"
            tags = []
            for prop_name, prop_value in properties.items():
                if prop_value.get("type") == "date" and prop_value.get("date"):
                    due_date = prop_value["date"]["start"]
                elif prop_value.get("type") == "select" and prop_value.get("select"):
                    priority = prop_value["select"]["name"]
                elif prop_value.get("type") == "multi_select" and prop_value.get("multi_select"):
                    tags = [tag["name"] for tag in prop_value["multi_select"]]
            task_data = {
                "user_id": current_user["id"],
                "notion_id": page["id"],
                "title": title,
                "due_date": due_date,
                "priority": priority,
                "tags": tags,
                "created_time": page["created_time"],
                "last_edited_time": page["last_edited_time"]
            }
            tasks.append(task_data)
        # Store tasks in Supabase
        if tasks:
            for task in tasks:
                existing = supabase.table("notion_tasks").select("*").eq("notion_id", task["notion_id"]).eq("user_id", current_user["id"]).execute()
                if existing.data:
                    supabase.table("notion_tasks").update(task).eq("notion_id", task["notion_id"]).eq("user_id", current_user["id"]).execute()
                else:
                    supabase.table("notion_tasks").insert(task).execute()
        return {
            "success": True,
            "database_id": request.database_id,
            "sync_type": request.sync_type,
            "tasks": tasks,
            "total_count": len(tasks)
        }

@router.post("/tasks/create", summary="Create a new task in Notion")
async def create_notion_task(
    request: NotionTaskSync,
    database_id: str,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    connection_result = supabase.table("notion_connections").select("*").eq("user_id", current_user["id"]).execute()
    if not connection_result.data:
        raise HTTPException(status_code=401, detail="Notion not connected")
    connection = connection_result.data[0]
    headers = {
        "Authorization": f"Bearer {connection['access_token']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    properties = {
        "Name": {
            "title": [
                {"text": {"content": request.title}}
            ]
        }
    }
    if request.description:
        properties["Description"] = {
            "rich_text": [
                {"text": {"content": request.description}}
            ]
        }
    if request.due_date:
        properties["Due Date"] = {"date": {"start": request.due_date}}
    if request.priority:
        properties["Priority"] = {"select": {"name": request.priority}}
    if request.tags:
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in request.tags]}
    page_data = {"parent": {"database_id": database_id}, "properties": properties}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_BASE}/pages",
            json=page_data,
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create task in Notion")
        created_page = response.json()
        # Store created task in Supabase
        task_data = {
            "user_id": current_user["id"],
            "notion_id": created_page["id"],
            "title": request.title,
            "due_date": request.due_date,
            "priority": request.priority,
            "tags": request.tags,
            "created_time": created_page["created_time"],
            "last_edited_time": created_page["created_time"]
        }
        supabase.table("notion_tasks").insert(task_data).execute()
        return {
            "success": True,
            "task_id": created_page["id"],
            "title": request.title,
            "created_time": created_page["created_time"]
        }

@router.post("/webhook", summary="Handle Notion webhook events")
async def handle_notion_webhook(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    webhook_data = await request.json()
    event_type = webhook_data.get("type")
    # Optionally store webhook events in Supabase for audit/logging
    supabase = get_supabase_client()
    event_data = {
        "user_id": current_user["id"],
        "event_type": event_type,
        "payload": webhook_data,
        "timestamp": datetime.now().isoformat()
    }
    supabase.table("notion_webhooks").insert(event_data).execute()
    if event_type == "page.updated":
        page_id = webhook_data.get("page", {}).get("id")
        return {
            "success": True,
            "event": "page_updated",
            "page_id": page_id,
            "timestamp": datetime.now().isoformat()
        }
    elif event_type == "database.updated":
        database_id = webhook_data.get("database", {}).get("id")
        return {
            "success": True,
            "event": "database_updated",
            "database_id": database_id,
            "timestamp": datetime.now().isoformat()
        }
    return {
        "success": True,
        "event": "unknown",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/status", summary="Get Notion connection status")
async def get_notion_status(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    connection_result = supabase.table("notion_connections").select("*").eq("user_id", current_user["id"]).execute()
    if not connection_result.data:
        return {"connected": False, "message": "Notion not connected"}
    connection = connection_result.data[0]
    return {
        "connected": True,
        "workspace_name": connection.get("workspace_name", ""),
        "connected_at": connection.get("connected_at"),
        "last_sync": connection.get("last_sync")
    }

@router.delete("/disconnect", summary="Disconnect Notion integration")
async def disconnect_notion(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    supabase.table("notion_connections").delete().eq("user_id", current_user["id"]).execute()
    supabase.table("notion_tasks").delete().eq("user_id", current_user["id"]).execute()
    return {"success": True, "message": "Notion disconnected successfully"} 