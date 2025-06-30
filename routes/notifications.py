from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from services.supabase import get_supabase_client
from services.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Pydantic models
class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    send_time: datetime
    type: str = Field(default="reminder", pattern="^(reminder|alert|system|goal|task)$")
    category: str = Field(default="task", pattern="^(task|goal|system|alert|schedule)$")
    repeat_interval: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|custom)$")
    is_read: bool = False
    is_sent: bool = False

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=1000)
    send_time: Optional[datetime] = None
    type: Optional[str] = Field(None, pattern="^(reminder|alert|system|goal|task)$")
    category: Optional[str] = Field(None, pattern="^(task|goal|system|alert|schedule)$")
    repeat_interval: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|custom)$")
    is_read: Optional[bool] = None
    is_sent: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# CRUD Operations
@router.post("/", response_model=NotificationResponse, summary="Create a new notification")
async def create_notification(
    notification: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification for the current user"""
    try:
        supabase = get_supabase_client()
        
        notification_data = {
            "user_id": current_user["id"],
            "title": notification.title,
            "message": notification.message,
            "send_time": notification.send_time.isoformat(),
            "type": notification.type,
            "category": notification.category,
            "repeat_interval": notification.repeat_interval,
            "is_read": notification.is_read,
            "is_sent": notification.is_sent,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("notifications").insert(notification_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        
        return NotificationResponse(**result.data[0])
    except Exception as e:
        logging.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[NotificationResponse], summary="Get all notifications for current user")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    is_read: Optional[bool] = None
):
    """Get all notifications for the current user with optional filtering"""
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("notifications").select("*").eq("user_id", current_user["id"])
        
        # Apply filters
        if category:
            query = query.eq("category", category)
        if is_read is not None:
            query = query.eq("is_read", is_read)
        
        # Apply pagination and ordering
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        if not result.data:
            return []
        
        return [NotificationResponse(**notification) for notification in result.data]
    except Exception as e:
        logging.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{notification_id}", response_model=NotificationResponse, summary="Get a specific notification")
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific notification by ID"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return NotificationResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}", response_model=NotificationResponse, summary="Update a notification")
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a notification"""
    try:
        supabase = get_supabase_client()
        
        # First check if notification exists and belongs to user
        existing = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if notification_update.title is not None:
            update_data["title"] = notification_update.title
        if notification_update.message is not None:
            update_data["message"] = notification_update.message
        if notification_update.send_time is not None:
            update_data["send_time"] = notification_update.send_time.isoformat()
        if notification_update.type is not None:
            update_data["type"] = notification_update.type
        if notification_update.category is not None:
            update_data["category"] = notification_update.category
        if notification_update.repeat_interval is not None:
            update_data["repeat_interval"] = notification_update.repeat_interval
        if notification_update.is_read is not None:
            update_data["is_read"] = notification_update.is_read
        if notification_update.is_sent is not None:
            update_data["is_sent"] = notification_update.is_sent
        
        result = supabase.table("notifications").update(update_data).eq("id", notification_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update notification")
        
        return NotificationResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}", summary="Delete a notification")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        supabase = get_supabase_client()
        
        # Check if notification exists and belongs to user
        existing = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        result = supabase.table("notifications").delete().eq("id", notification_id).execute()
        
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        supabase = get_supabase_client()
        
        # Check if notification exists and belongs to user
        existing = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        result = supabase.table("notifications").update({
            "is_read": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).execute()
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/unread", summary="Mark notification as unread")
async def mark_notification_unread(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as unread"""
    try:
        supabase = get_supabase_client()
        
        # Check if notification exists and belongs to user
        existing = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        result = supabase.table("notifications").update({
            "is_read": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).execute()
        
        return {"message": "Notification marked as unread"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error marking notification as unread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread/count", summary="Get unread notification count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get the count of unread notifications for the current user"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("notifications").select("id", count="exact").eq("user_id", current_user["id"]).eq("is_read", False).execute()
        
        return {"unread_count": result.count or 0}
    except Exception as e:
        logging.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming", response_model=List[NotificationResponse], summary="Get upcoming notifications")
async def get_upcoming_notifications(
    current_user: dict = Depends(get_current_user),
    hours: int = 24
):
    """Get notifications scheduled within the next N hours"""
    try:
        supabase = get_supabase_client()
        
        now = datetime.utcnow()
        future_time = now + timedelta(hours=hours)
        
        result = supabase.table("notifications").select("*").eq("user_id", current_user["id"]).gte("send_time", now.isoformat()).lte("send_time", future_time.isoformat()).order("send_time").execute()
        
        if not result.data:
            return []
        
        return [NotificationResponse(**notification) for notification in result.data]
    except Exception as e:
        logging.error(f"Error fetching upcoming notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/mark-read", summary="Mark multiple notifications as read")
async def mark_multiple_read(
    notification_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Mark multiple notifications as read"""
    try:
        supabase = get_supabase_client()
        
        # Verify all notifications belong to the user
        for notification_id in notification_ids:
            existing = supabase.table("notifications").select("*").eq("id", notification_id).eq("user_id", current_user["id"]).execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
        
        # Update all notifications
        result = supabase.table("notifications").update({
            "is_read": True,
            "updated_at": datetime.utcnow().isoformat()
        }).in_("id", notification_ids).execute()
        
        return {"message": f"Marked {len(notification_ids)} notifications as read"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error marking multiple notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 