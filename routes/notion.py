from fastapi import APIRouter, HTTPException, Depends, Request, Header, status
from typing import Dict, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, HttpUrl, ConfigDict
from services.supabase import get_supabase_client
from services.auth import get_current_user
import httpx
import json
import os
from urllib.parse import urlencode
import logging
import hmac
import hashlib

from services.notion import NotionClient, NotionFlashcardGenerator, NotionSyncManager
from services.ai.openai_service import get_openai_service
from services.notion.rate_limited_queue import get_notion_queue

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notion", tags=["Notion Sync"])

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

class FlashcardGenerationRequest(BaseModel):
    """Flashcard generation request."""
    model_config = ConfigDict(from_attributes=True)
    
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    count: int = 5
    difficulty: str = "medium"

class SyncRequest(BaseModel):
    """Sync request."""
    model_config = ConfigDict(from_attributes=True)
    
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    sync_direction: str = "notion_to_cognie"  # "notion_to_cognie", "cognie_to_notion", "bidirectional"

class NotionPageInfo(BaseModel):
    """Notion page information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    url: str
    last_edited_time: datetime
    parent_type: Optional[str] = None

class SyncStatusResponse(BaseModel):
    """Sync status response."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    notion_page_id: str
    last_sync_time: datetime
    sync_direction: str
    status: str
    error_message: Optional[str] = None
    items_synced: int

class NotionWebhookEvent(BaseModel):
    """Notion webhook event model."""
    model_config = ConfigDict(from_attributes=True)
    
    type: str  # page.updated, database.updated, etc.
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    last_edited_time: Optional[str] = None
    user_id: Optional[str] = None

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

# Dependency to get Notion client
async def get_notion_client(current_user: dict = Depends(get_current_user)) -> NotionClient:
    """Get Notion client for the current user."""
    try:
        # Get user's Notion API key from database
        supabase = get_supabase_client()
        result = supabase.table("user_settings").select("notion_api_key").eq("user_id", current_user["id"]).execute()
        
        if not result.data or not result.data[0].get("notion_api_key"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notion API key not configured. Please set up Notion integration first."
            )
        
        api_key = result.data[0]["notion_api_key"]
        return NotionClient(api_key=api_key)
        
    except Exception as e:
        logger.error(f"Failed to get Notion client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Notion client"
        )

# Dependency to get AI service
async def get_ai_service():
    """Get OpenAI service."""
    return get_openai_service()

def verify_notion_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Notion webhook signature."""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

@router.post("/auth", summary="Authenticate with Notion")
async def authenticate_notion(
    auth_request: NotionAuthRequest,
    current_user: dict = Depends(get_current_user)
):
    """Authenticate with Notion and save API key."""
    try:
        # Test the API key by making a simple request
        notion_client = NotionClient(api_key=auth_request.api_key)
        
        # Try to get user info (this will fail if API key is invalid)
        await notion_client.search(query="", filter_params={"property": "object", "value": "page"})
        
        # Save API key to user settings
        supabase = get_supabase_client()
        supabase.table("user_settings").upsert({
            "user_id": current_user["id"],
            "notion_api_key": auth_request.api_key,
            "updated_at": datetime.now(UTC).isoformat()
        }).execute()
        
        return {"message": "Notion authentication successful", "status": "connected"}
        
    except Exception as e:
        logger.error(f"Notion authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Notion API key or authentication failed"
        )

@router.get("/pages", summary="Get user's Notion pages")
async def get_notion_pages(
    notion_client: NotionClient = Depends(get_notion_client)
):
    """Get user's Notion pages and databases."""
    try:
        # Search for pages and databases
        pages = await notion_client.search(
            query="",
            filter_params={"property": "object", "value": "page"}
        )
        
        databases = await notion_client.search(
            query="",
            filter_params={"property": "object", "value": "database"}
        )
        
        # Format response
        page_list = []
        for page in pages:
            title = "Untitled"
            if "properties" in page:
                for prop_name, prop_data in page["properties"].items():
                    if prop_data.get("type") == "title" and prop_data.get("title"):
                        title = "".join([text.get("plain_text", "") for text in prop_data["title"]])
                        break
            
            page_list.append(NotionPageInfo(
                id=page["id"],
                title=title,
                url=page.get("url", ""),
                last_edited_time=datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00")),
                parent_type=page.get("parent", {}).get("type")
            ))
        
        return {
            "pages": page_list,
            "total_pages": len(page_list),
            "total_databases": len(databases)
        }
        
    except Exception as e:
        logger.error(f"Failed to get Notion pages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Notion pages"
        )

@router.post("/generate-flashcards", summary="Generate flashcards from Notion content")
async def generate_flashcards(
    request: FlashcardGenerationRequest,
    current_user: dict = Depends(get_current_user),
    notion_client: NotionClient = Depends(get_notion_client),
    ai_service = Depends(get_ai_service)
):
    """Generate flashcards from Notion page or database."""
    try:
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        
        if request.page_id:
            # Generate from page
            flashcards = await flashcard_generator.generate_flashcards_from_page(
                page_id=request.page_id,
                count=request.count,
                difficulty=request.difficulty
            )
        elif request.database_id:
            # Generate from database
            flashcards = await flashcard_generator.generate_flashcards_from_database(
                database_id=request.database_id,
                count=request.count,
                difficulty=request.difficulty
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either page_id or database_id must be provided"
            )
        
        # Convert to response format
        flashcard_list = []
        for flashcard in flashcards:
            flashcard_list.append({
                "question": flashcard.question,
                "answer": flashcard.answer,
                "tags": flashcard.tags,
                "difficulty": flashcard.difficulty,
                "source_page_id": flashcard.source_page_id,
                "source_page_title": flashcard.source_page_title
            })
        
        return {
            "flashcards": flashcard_list,
            "count": len(flashcard_list),
            "source_type": "page" if request.page_id else "database",
            "source_id": request.page_id or request.database_id
        }
        
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

@router.post("/sync", summary="Sync Notion content with Cognie")
async def sync_notion_content(
    request: SyncRequest,
    current_user: dict = Depends(get_current_user),
    notion_client: NotionClient = Depends(get_notion_client),
    ai_service = Depends(get_ai_service)
):
    """Sync Notion content with Cognie flashcards."""
    try:
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        sync_manager = NotionSyncManager(notion_client, flashcard_generator)
        
        if request.page_id:
            # Sync page
            sync_status = await sync_manager.sync_page_to_flashcards(
                user_id=current_user["id"],
                notion_page_id=request.page_id,
                sync_direction=request.sync_direction
            )
        elif request.database_id:
            # Sync database
            sync_status = await sync_manager.sync_database_to_flashcards(
                user_id=current_user["id"],
                notion_database_id=request.database_id,
                sync_direction=request.sync_direction
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either page_id or database_id must be provided"
            )
        
        return SyncStatusResponse(
            user_id=sync_status.user_id,
            notion_page_id=sync_status.notion_page_id,
            last_sync_time=sync_status.last_sync_time,
            sync_direction=sync_status.sync_direction,
            status=sync_status.status,
            error_message=sync_status.error_message,
            items_synced=sync_status.items_synced
        )
        
    except Exception as e:
        logger.error(f"Failed to sync Notion content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync content: {str(e)}"
        )

@router.get("/sync-status/{page_id}", summary="Get sync status for a page")
async def get_sync_status(
    page_id: str,
    current_user: dict = Depends(get_current_user),
    notion_client: NotionClient = Depends(get_notion_client),
    ai_service = Depends(get_ai_service)
):
    """Get sync status for a specific Notion page."""
    try:
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        sync_manager = NotionSyncManager(notion_client, flashcard_generator)
        
        sync_status = await sync_manager.get_sync_status(current_user["id"], page_id)
        
        if not sync_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sync status found for this page"
            )
        
        return SyncStatusResponse(
            user_id=sync_status.user_id,
            notion_page_id=sync_status.notion_page_id,
            last_sync_time=sync_status.last_sync_time,
            sync_direction=sync_status.sync_direction,
            status=sync_status.status,
            error_message=sync_status.error_message,
            items_synced=sync_status.items_synced
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync status"
        )

@router.get("/sync-history", summary="Get user's sync history")
async def get_sync_history(
    current_user: dict = Depends(get_current_user),
    notion_client: NotionClient = Depends(get_notion_client),
    ai_service = Depends(get_ai_service)
):
    """Get user's Notion sync history."""
    try:
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        sync_manager = NotionSyncManager(notion_client, flashcard_generator)
        
        sync_history = await sync_manager.get_user_sync_history(current_user["id"])
        
        return {
            "sync_history": [
                SyncStatusResponse(
                    user_id=status.user_id,
                    notion_page_id=status.notion_page_id,
                    last_sync_time=status.last_sync_time,
                    sync_direction=status.sync_direction,
                    status=status.status,
                    error_message=status.error_message,
                    items_synced=status.items_synced
                )
                for status in sync_history
            ],
            "total_syncs": len(sync_history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync history"
        )

@router.post("/generate-from-text", summary="Generate flashcards from text input")
async def generate_flashcards_from_text(
    text: str,
    title: str = "Manual Input",
    count: int = 5,
    difficulty: str = "medium",
    current_user: dict = Depends(get_current_user),
    notion_client: NotionClient = Depends(get_notion_client),
    ai_service = Depends(get_ai_service)
):
    """Generate flashcards from plain text input."""
    try:
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        
        flashcards = await flashcard_generator.generate_flashcards_from_text(
            text=text,
            title=title,
            count=count,
            difficulty=difficulty
        )
        
        # Convert to response format
        flashcard_list = []
        for flashcard in flashcards:
            flashcard_list.append({
                "question": flashcard.question,
                "answer": flashcard.answer,
                "tags": flashcard.tags,
                "difficulty": flashcard.difficulty,
                "source_page_id": flashcard.source_page_id,
                "source_page_title": flashcard.source_page_title
            })
        
        return {
            "flashcards": flashcard_list,
            "count": len(flashcard_list),
            "source_type": "text",
            "title": title
        }
        
    except Exception as e:
        logger.error(f"Failed to generate flashcards from text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

# Webhook endpoints
@router.post("/webhook/notion", summary="Receive Notion webhooks")
async def receive_notion_webhook(
    request: Request,
    x_notion_signature: str = Header(None),
    x_notion_timestamp: str = Header(None)
):
    """Receive webhooks from Notion when pages/databases change."""
    try:
        # Get webhook body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Verify webhook signature (if signature is provided)
        if x_notion_signature:
            # Get webhook secret from environment
            webhook_secret = os.getenv("NOTION_WEBHOOK_SECRET")
            if webhook_secret and not verify_notion_webhook_signature(body, x_notion_signature, webhook_secret):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
        
        # Parse webhook event
        try:
            event_data = json.loads(body_str)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook body")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")
        
        # Extract event information
        event_type = event_data.get("type")
        page_id = event_data.get("page", {}).get("id")
        database_id = event_data.get("database", {}).get("id")
        last_edited_time = event_data.get("page", {}).get("last_edited_time") or event_data.get("database", {}).get("last_edited_time")
        
        logger.info(f"Received Notion webhook: {event_type} for {'page' if page_id else 'database'} {page_id or database_id}")
        
        # Process webhook based on event type
        if event_type in ["page.updated", "database.updated"]:
            # Queue sync operation using rate-limited queue
            await queue_notion_sync(page_id, database_id, last_edited_time)
        
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing Notion webhook: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing failed")

@router.get("/webhook/notion/verify", summary="Verify Notion webhook")
async def verify_notion_webhook(challenge: str):
    """Verify Notion webhook subscription."""
    return {"challenge": challenge}

async def queue_notion_sync(page_id: Optional[str], database_id: Optional[str], last_edited_time: Optional[str]):
    """Queue a Notion sync operation using the rate-limited queue."""
    try:
        # Get all users who have this page/database synced
        supabase = get_supabase_client()
        
        if page_id:
            # Find users who have synced this page
            result = supabase.table("flashcards").select("user_id").eq("source_page_id", page_id).execute()
        elif database_id:
            # Find users who have synced this database
            result = supabase.table("flashcards").select("user_id").eq("source_database_id", database_id).execute()
        else:
            return
        
        user_ids = list(set([item["user_id"] for item in result.data]))
        
        # Queue sync for each user
        for user_id in user_ids:
            # Get user's Notion client
            user_settings = supabase.table("user_settings").select("notion_api_key").eq("user_id", user_id).execute()
            
            if user_settings.data and user_settings.data[0].get("notion_api_key"):
                notion_client = NotionClient(api_key=user_settings.data[0]["notion_api_key"])
                notion_queue = get_notion_queue(notion_client)
                
                # Queue the sync operation
                await notion_queue.enqueue_request(
                    method="POST",
                    endpoint="/internal/sync",
                    data={
                        "user_id": user_id,
                        "page_id": page_id,
                        "database_id": database_id,
                        "last_edited_time": last_edited_time
                    }
                )
        
        logger.info(f"Queued sync for {len(user_ids)} users")
        
    except Exception as e:
        logger.error(f"Error queuing Notion sync: {e}")

@router.post("/internal/sync", summary="Internal sync endpoint for webhook processing")
async def internal_sync(
    user_id: str,
    page_id: Optional[str] = None,
    database_id: Optional[str] = None,
    last_edited_time: Optional[str] = None
):
    """Internal endpoint for processing queued sync operations from webhooks."""
    try:
        # Get user's Notion client
        supabase = get_supabase_client()
        user_settings = supabase.table("user_settings").select("notion_api_key").eq("user_id", user_id).execute()
        
        if not user_settings.data or not user_settings.data[0].get("notion_api_key"):
            logger.error(f"No Notion API key found for user {user_id}")
            return {"status": "error", "message": "No Notion API key configured"}
        
        notion_client = NotionClient(api_key=user_settings.data[0]["notion_api_key"])
        ai_service = get_openai_service()
        flashcard_generator = NotionFlashcardGenerator(notion_client, ai_service)
        sync_manager = NotionSyncManager(notion_client, flashcard_generator)
        
        # Check if we've already synced this recently (debounce)
        if last_edited_time:
            last_sync = supabase.table("notion_sync_status").select("last_sync_time").eq("user_id", user_id).eq("notion_page_id", page_id or database_id).execute()
            
            if last_sync.data:
                last_sync_time = datetime.fromisoformat(last_sync.data[0]["last_sync_time"].replace("Z", "+00:00"))
                webhook_time = datetime.fromisoformat(last_edited_time.replace("Z", "+00:00"))
                
                # If last sync was within 30 seconds of webhook time, skip (debounce)
                if abs((last_sync_time - webhook_time).total_seconds()) < 30:
                    logger.info(f"Skipping sync for user {user_id}, page {page_id or database_id} - too recent")
                    return {"status": "skipped", "message": "Sync too recent"}
        
        # Perform sync
        if page_id:
            sync_status = await sync_manager.sync_page_to_flashcards(
                user_id=user_id,
                notion_page_id=page_id,
                sync_direction="notion_to_cognie"
            )
        elif database_id:
            sync_status = await sync_manager.sync_database_to_flashcards(
                user_id=user_id,
                notion_database_id=database_id,
                sync_direction="notion_to_cognie"
            )
        else:
            return {"status": "error", "message": "No page_id or database_id provided"}
        
        logger.info(f"Internal sync completed for user {user_id}, page {page_id or database_id}")
        return {"status": "success", "items_synced": sync_status.items_synced}
        
    except Exception as e:
        logger.error(f"Internal sync failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e)}

# Import os for environment variables
import os 