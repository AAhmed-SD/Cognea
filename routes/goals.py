"""
Goals router for the Personal Agent application.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from models.goal import Goal, GoalCreate, GoalUpdate, PriorityLevel
from services.supabase import get_supabase_client
from services.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])

logger = logging.getLogger(__name__)

@router.post("/", response_model=Goal, summary="Create a new goal")
async def create_goal(
    goal: GoalCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new goal for the current user."""
    try:
        supabase = get_supabase_client()
        
        goal_data = {
            "user_id": str(goal.user_id),
            "title": goal.title,
            "description": goal.description,
            "due_date": goal.due_date.isoformat() if goal.due_date else None,
            "priority": goal.priority.value,
            "is_starred": goal.is_starred,
            "status": "Not Started",
            "progress": 0,
            "analytics": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("goals").insert(goal_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create goal")
        
        created_goal = result.data[0]
        return Goal(**created_goal)
        
    except Exception as e:
        logger.error(f"Error creating goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create goal")

@router.get("/", response_model=List[Goal], summary="Get all goals for user")
async def get_goals(
    current_user: dict = Depends(get_current_user),
    priority: Optional[PriorityLevel] = Query(None, description="Filter by priority"),
    is_starred: Optional[bool] = Query(None, description="Filter by starred status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of goals to return"),
    offset: int = Query(0, ge=0, description="Number of goals to skip")
):
    """Get all goals for the current user with optional filtering."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("goals").select("*").eq("user_id", current_user["id"])
        
        if priority:
            query = query.eq("priority", priority.value)
        if is_starred is not None:
            query = query.eq("is_starred", is_starred)
            
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()
        
        goals = [Goal(**goal) for goal in result.data]
        return goals
        
    except Exception as e:
        logger.error(f"Error fetching goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch goals")

@router.get("/{goal_id}", response_model=Goal, summary="Get a specific goal")
async def get_goal(
    goal_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific goal by ID."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("goals").select("*").eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return Goal(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch goal")

@router.put("/{goal_id}", response_model=Goal, summary="Update a goal")
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a specific goal."""
    try:
        supabase = get_supabase_client()
        
        # First check if goal exists and belongs to user
        existing = supabase.table("goals").select("*").eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if goal_update.title is not None:
            update_data["title"] = goal_update.title
        if goal_update.description is not None:
            update_data["description"] = goal_update.description
        if goal_update.due_date is not None:
            update_data["due_date"] = goal_update.due_date.isoformat()
        if goal_update.priority is not None:
            update_data["priority"] = goal_update.priority.value
        if goal_update.status is not None:
            update_data["status"] = goal_update.status
        if goal_update.progress is not None:
            update_data["progress"] = goal_update.progress
        if goal_update.is_starred is not None:
            update_data["is_starred"] = goal_update.is_starred
        if goal_update.analytics is not None:
            update_data["analytics"] = goal_update.analytics
        
        result = supabase.table("goals").update(update_data).eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update goal")
        
        return Goal(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update goal")

@router.delete("/{goal_id}", summary="Delete a goal")
async def delete_goal(
    goal_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific goal."""
    try:
        supabase = get_supabase_client()
        
        # Check if goal exists and belongs to user
        existing = supabase.table("goals").select("*").eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        result = supabase.table("goals").delete().eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        return {"message": "Goal deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete goal")

@router.post("/{goal_id}/star", response_model=Goal, summary="Star/unstar a goal")
async def toggle_goal_star(
    goal_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Toggle the starred status of a goal."""
    try:
        supabase = get_supabase_client()
        
        # Get current goal
        existing = supabase.table("goals").select("*").eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        current_goal = existing.data[0]
        new_starred_status = not current_goal.get("is_starred", False)
        
        update_data = {
            "is_starred": new_starred_status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("goals").update(update_data).eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        return Goal(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling goal star {goal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle goal star")

@router.post("/{goal_id}/progress", response_model=Goal, summary="Update goal progress")
async def update_goal_progress(
    goal_id: UUID,
    progress: int = Query(..., ge=0, le=100, description="Progress percentage (0-100)"),
    current_user: dict = Depends(get_current_user)
):
    """Update the progress of a goal."""
    try:
        supabase = get_supabase_client()
        
        update_data = {
            "progress": progress,
            "status": "Completed" if progress >= 100 else "In Progress" if progress > 0 else "Not Started",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("goals").update(update_data).eq("id", str(goal_id)).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return Goal(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal progress {goal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update goal progress")

@router.get("/stats/summary", summary="Get goal statistics")
async def get_goal_stats(current_user: dict = Depends(get_current_user)):
    """Get goal statistics for the current user."""
    try:
        supabase = get_supabase_client()
        
        # Get all goals for user
        result = supabase.table("goals").select("*").eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            return {
                "total_goals": 0,
                "completed_goals": 0,
                "in_progress_goals": 0,
                "not_started_goals": 0,
                "starred_goals": 0,
                "average_progress": 0.0
            }
        
        goals = result.data
        total_goals = len(goals)
        completed_goals = len([g for g in goals if g["status"] == "Completed"])
        in_progress_goals = len([g for g in goals if g["status"] == "In Progress"])
        not_started_goals = len([g for g in goals if g["status"] == "Not Started"])
        starred_goals = len([g for g in goals if g.get("is_starred", False)])
        
        total_progress = sum(g.get("progress", 0) for g in goals)
        average_progress = (total_progress / total_goals) if total_goals > 0 else 0
        
        return {
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "in_progress_goals": in_progress_goals,
            "not_started_goals": not_started_goals,
            "starred_goals": starred_goals,
            "average_progress": round(average_progress, 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching goal stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch goal statistics") 