"""
Tasks router for the Personal Agent application.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from models.task import PriorityLevel, Task, TaskCreate, TaskStatus, TaskUpdate
from services.auth import get_current_user
from services.supabase import get_supabase_client

router = APIRouter(tags=["Tasks"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=Task, summary="Create a new task")
async def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Create a new task for the current user."""
    try:
        supabase = get_supabase_client()

        task_data = {
            "user_id": str(task.user_id),
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority.value,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = supabase.table("tasks").insert(task_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create task")

        created_task = result.data[0]
        return Task(**created_task)

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/", response_model=list[Task], summary="Get all tasks for user")
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    priority: PriorityLevel | None = Query(None, description="Filter by priority"),
    limit: int = Query(100, ge=1, le=1000, description="Number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
):
    """Get all tasks for the current user with optional filtering."""
    try:
        supabase = get_supabase_client()

        query = supabase.table("tasks").select("*").eq("user_id", current_user["id"])

        if status:
            query = query.eq("status", status.value)
        if priority:
            query = query.eq("priority", priority.value)

        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()

        tasks = [Task(**task) for task in result.data]
        return tasks

    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


@router.get("/{task_id}", response_model=Task, summary="Get a specific task")
async def get_task(task_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get a specific task by ID."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("tasks")
            .select("*")
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return Task(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")


@router.put("/{task_id}", response_model=Task, summary="Update a task")
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a specific task."""
    try:
        supabase = get_supabase_client()

        # First check if task exists and belongs to user
        existing = (
            supabase.table("tasks")
            .select("*")
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # Prepare update data
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if task_update.title is not None:
            update_data["title"] = task_update.title
        if task_update.description is not None:
            update_data["description"] = task_update.description
        if task_update.status is not None:
            update_data["status"] = task_update.status.value
        if task_update.due_date is not None:
            update_data["due_date"] = task_update.due_date.isoformat()
        if task_update.priority is not None:
            update_data["priority"] = task_update.priority.value

        result = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update task")

        return Task(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/{task_id}", summary="Delete a task")
async def delete_task(task_id: UUID, current_user: dict = Depends(get_current_user)):
    """Delete a specific task."""
    try:
        supabase = get_supabase_client()

        # Check if task exists and belongs to user
        existing = (
            supabase.table("tasks")
            .select("*")
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found")

        result = (  # noqa: F841
            supabase.table("tasks")
            .delete()
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


@router.post(
    "/{task_id}/complete", response_model=Task, summary="Mark task as completed"
)
async def complete_task(task_id: UUID, current_user: dict = Depends(get_current_user)):
    """Mark a task as completed."""
    try:
        supabase = get_supabase_client()

        update_data = {
            "status": TaskStatus.COMPLETED.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", str(task_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return Task(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete task")


@router.get("/stats/summary", summary="Get task statistics")
async def get_task_stats(current_user: dict = Depends(get_current_user)):
    """Get task statistics for the current user."""
    try:
        supabase = get_supabase_client()

        # Get all tasks for user
        result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "in_progress_tasks": 0,
                "completion_rate": 0.0,
            }

        tasks = result.data
        total_tasks = len(tasks)
        completed_tasks = len(
            [t for t in tasks if t["status"] == TaskStatus.COMPLETED.value]
        )
        pending_tasks = len(
            [t for t in tasks if t["status"] == TaskStatus.PENDING.value]
        )
        in_progress_tasks = len(
            [t for t in tasks if t["status"] == TaskStatus.IN_PROGRESS.value]
        )

        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": round(completion_rate, 2),
        }

    except Exception as e:
        logger.error(f"Error fetching task stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task statistics")
