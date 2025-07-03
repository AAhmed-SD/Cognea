"""
Schedule Blocks router for the Personal Agent application.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from models.schedule_block import (
    ScheduleBlock,
    ScheduleBlockCreate,
    ScheduleBlockUpdate,
)
from services.auth import get_current_user
from services.supabase import get_supabase_client

router = APIRouter(prefix="/schedule-blocks", tags=["Schedule Blocks"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=ScheduleBlock, summary="Create a new schedule block")
async def create_schedule_block(
    schedule_block: ScheduleBlockCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new schedule block for the current user."""
    try:
        supabase = get_supabase_client()

        # Validate time range
        if schedule_block.start_time >= schedule_block.end_time:
            raise HTTPException(
                status_code=400, detail="Start time must be before end time"
            )

        schedule_data = {
            "user_id": str(schedule_block.user_id),
            "title": schedule_block.title,
            "description": schedule_block.description,
            "start_time": schedule_block.start_time.isoformat(),
            "end_time": schedule_block.end_time.isoformat(),
            "context": schedule_block.context,
            "goal_id": str(schedule_block.goal_id) if schedule_block.goal_id else None,
            "is_fixed": schedule_block.is_fixed,
            "is_rescheduled": schedule_block.is_rescheduled,
            "rescheduled_count": schedule_block.rescheduled_count,
            "color_code": schedule_block.color_code,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("schedule_blocks").insert(schedule_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create schedule block"
            )

        created_block = result.data[0]
        return ScheduleBlock(**created_block)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule block")


@router.get(
    "/", response_model=list[ScheduleBlock], summary="Get schedule blocks for user"
)
async def get_schedule_blocks(
    current_user: dict = Depends(get_current_user),
    start_date: datetime | None = Query(
        None, description="Filter blocks starting from this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter blocks ending before this date"
    ),
    context: str | None = Query(
        None, description="Filter by context (e.g., 'Work', 'Study')"
    ),
    goal_id: UUID | None = Query(None, description="Filter by associated goal"),
    limit: int = Query(100, ge=1, le=1000, description="Number of blocks to return"),
    offset: int = Query(0, ge=0, description="Number of blocks to skip"),
):
    """Get schedule blocks for the current user with optional filtering."""
    try:
        supabase = get_supabase_client()

        query = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
        )

        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("end_time", end_date.isoformat())
        if context:
            query = query.eq("context", context)
        if goal_id:
            query = query.eq("goal_id", str(goal_id))

        query = query.range(offset, offset + limit - 1).order("start_time", desc=False)
        result = query.execute()

        blocks = [ScheduleBlock(**block) for block in result.data]
        return blocks

    except Exception as e:
        logger.error(f"Error fetching schedule blocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule blocks")


@router.get(
    "/today", response_model=list[ScheduleBlock], summary="Get today's schedule blocks"
)
async def get_today_schedule_blocks(current_user: dict = Depends(get_current_user)):
    """Get all schedule blocks for today."""
    try:
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        supabase = get_supabase_client()
        result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("start_time", start_of_day.isoformat())
            .lte("end_time", end_of_day.isoformat())
            .order("start_time", desc=False)
            .execute()
        )

        blocks = [ScheduleBlock(**block) for block in result.data]
        return blocks

    except Exception as e:
        logger.error(f"Error fetching today's schedule blocks: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch today's schedule blocks"
        )


@router.get(
    "/{block_id}", response_model=ScheduleBlock, summary="Get a specific schedule block"
)
async def get_schedule_block(
    block_id: UUID, current_user: dict = Depends(get_current_user)
):
    """Get a specific schedule block by ID."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        return ScheduleBlock(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule block {block_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule block")


@router.put(
    "/{block_id}", response_model=ScheduleBlock, summary="Update a schedule block"
)
async def update_schedule_block(
    block_id: UUID,
    schedule_block_update: ScheduleBlockUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a specific schedule block."""
    try:
        supabase = get_supabase_client()

        # First check if block exists and belongs to user
        existing = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if schedule_block_update.title is not None:
            update_data["title"] = schedule_block_update.title
        if schedule_block_update.description is not None:
            update_data["description"] = schedule_block_update.description
        if schedule_block_update.start_time is not None:
            update_data["start_time"] = schedule_block_update.start_time.isoformat()
        if schedule_block_update.end_time is not None:
            update_data["end_time"] = schedule_block_update.end_time.isoformat()
        if schedule_block_update.context is not None:
            update_data["context"] = schedule_block_update.context
        if schedule_block_update.goal_id is not None:
            update_data["goal_id"] = str(schedule_block_update.goal_id)
        if schedule_block_update.is_fixed is not None:
            update_data["is_fixed"] = schedule_block_update.is_fixed
        if schedule_block_update.is_rescheduled is not None:
            update_data["is_rescheduled"] = schedule_block_update.is_rescheduled
        if schedule_block_update.rescheduled_count is not None:
            update_data["rescheduled_count"] = schedule_block_update.rescheduled_count
        if schedule_block_update.color_code is not None:
            update_data["color_code"] = schedule_block_update.color_code

        # Validate time range if both times are being updated
        if schedule_block_update.start_time and schedule_block_update.end_time:
            if schedule_block_update.start_time >= schedule_block_update.end_time:
                raise HTTPException(
                    status_code=400, detail="Start time must be before end time"
                )

        result = (
            supabase.table("schedule_blocks")
            .update(update_data)
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to update schedule block"
            )

        return ScheduleBlock(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule block {block_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule block")


@router.delete("/{block_id}", summary="Delete a schedule block")
async def delete_schedule_block(
    block_id: UUID, current_user: dict = Depends(get_current_user)
):
    """Delete a specific schedule block."""
    try:
        supabase = get_supabase_client()

        # Check if block exists and belongs to user
        existing = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        result = (  # noqa: F841
            supabase.table("schedule_blocks")
            .delete()
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {"message": "Schedule block deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule block {block_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule block")


@router.post(
    "/{block_id}/reschedule", response_model=ScheduleBlock, summary="Reschedule a block"
)
async def reschedule_block(
    block_id: UUID,
    new_start_time: datetime = Query(..., description="New start time"),
    new_end_time: datetime = Query(..., description="New end time"),
    current_user: dict = Depends(get_current_user),
):
    """Reschedule a block to new times."""
    try:
        if new_start_time >= new_end_time:
            raise HTTPException(
                status_code=400, detail="Start time must be before end time"
            )

        supabase = get_supabase_client()

        # Get current block
        existing = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        current_block = existing.data[0]
        current_rescheduled_count = current_block.get("rescheduled_count", 0)

        update_data = {
            "start_time": new_start_time.isoformat(),
            "end_time": new_end_time.isoformat(),
            "is_rescheduled": True,
            "rescheduled_count": current_rescheduled_count + 1,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = (
            supabase.table("schedule_blocks")
            .update(update_data)
            .eq("id", str(block_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return ScheduleBlock(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling block {block_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reschedule block")


@router.get("/stats/summary", summary="Get schedule block statistics")
async def get_schedule_stats(
    current_user: dict = Depends(get_current_user),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
):
    """Get schedule block statistics for the current user."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        supabase = get_supabase_client()
        result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("start_time", start_date.isoformat())
            .lte("end_time", end_date.isoformat())
            .execute()
        )

        if not result.data:
            return {
                "total_blocks": 0,
                "total_hours": 0,
                "rescheduled_blocks": 0,
                "context_breakdown": {},
                "average_block_duration": 0,
            }

        blocks = result.data
        total_blocks = len(blocks)
        rescheduled_blocks = len([b for b in blocks if b.get("is_rescheduled", False)])

        # Calculate total hours and context breakdown
        total_hours = 0
        context_breakdown = {}

        for block in blocks:
            start = datetime.fromisoformat(block["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(block["end_time"].replace("Z", "+00:00"))
            duration = (end - start).total_seconds() / 3600  # Convert to hours
            total_hours += duration

            context = block.get("context", "Unknown")
            context_breakdown[context] = context_breakdown.get(context, 0) + duration

        average_block_duration = total_hours / total_blocks if total_blocks > 0 else 0

        return {
            "total_blocks": total_blocks,
            "total_hours": round(total_hours, 2),
            "rescheduled_blocks": rescheduled_blocks,
            "context_breakdown": {k: round(v, 2) for k, v in context_breakdown.items()},
            "average_block_duration": round(average_block_duration, 2),
        }

    except Exception as e:
        logger.error(f"Error fetching schedule stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch schedule statistics"
        )
