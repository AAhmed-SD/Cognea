from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict
from datetime import datetime, timedelta
from services.audit import log_audit_from_request, AuditAction
from services.supabase import get_supabase_client
from services.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics & Trends"])

# In-memory storage for analytics data
user_analytics_db: Dict[int, dict] = {}
user_trends_db: Dict[int, list] = {}
user_weekly_reviews_db: Dict[int, dict] = {}
user_productivity_patterns_db: Dict[int, dict] = {}


@router.get(
    "/dashboard", summary="Personalized dashboard (habits, mood, focus time, goals)"
)
async def analytics_dashboard(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get personalized dashboard data from actual user data."""
    try:
        supabase = get_supabase_client()
        user_id = current_user["id"]

        # Get tasks data
        tasks_result = (
            supabase.table("tasks").select("*").eq("user_id", user_id).execute()
        )
        tasks = tasks_result.data or []

        # Get goals data
        goals_result = (
            supabase.table("goals").select("*").eq("user_id", user_id).execute()
        )
        goals = goals_result.data or []

        # Get schedule blocks data
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        schedule_blocks = schedule_result.data or []

        # Calculate focus time for last 7 days
        focus_time = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
            day_blocks = [
                block
                for block in schedule_blocks
                if block.get("start_time", "").startswith(date)
            ]
            total_minutes = sum(
                (
                    datetime.fromisoformat(block["end_time"].replace("Z", "+00:00"))
                    - datetime.fromisoformat(block["start_time"].replace("Z", "+00:00"))
                ).total_seconds()
                / 60
                for block in day_blocks
            )
            focus_time.append({"date": date, "minutes": int(total_minutes)})

        # Get completed vs pending tasks
        completed_tasks = [task for task in tasks if task.get("status") == "completed"]
        pending_tasks = [
            task for task in tasks if task.get("status") in ["pending", "in_progress"]
        ]

        dashboard = {
            "habits": [
                goal["title"] for goal in goals if goal.get("category") == "habit"
            ],
            "focus_time": focus_time,
            "goals": [goal["title"] for goal in goals],
            "task_stats": {
                "total": len(tasks),
                "completed": len(completed_tasks),
                "pending": len(pending_tasks),
                "completion_rate": (
                    len(completed_tasks) / len(tasks) * 100 if tasks else 0
                ),
            },
            "productivity_score": calculate_productivity_score(
                tasks, schedule_blocks, goals
            ),
        }

        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=AuditAction.READ,
            resource="analytics_dashboard",
        )

        return {"user_id": user_id, "dashboard": dashboard}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load dashboard: {str(e)}"
        )


@router.get(
    "/trends", summary="Visual insights over time (calendar heatmap, bar charts)"
)
async def trends(request: Request, current_user: dict = Depends(get_current_user)):
    """Get trend data for visualizations."""
    try:
        supabase = get_supabase_client()
        user_id = current_user["id"]

        # Get last 30 days of data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Get tasks with completion dates
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .execute()
        )
        tasks = tasks_result.data or []

        # Calculate daily productivity scores
        trends = []
        for i in range(30):
            date = (end_date - timedelta(days=i)).date().isoformat()
            day_tasks = [
                task for task in tasks if task.get("created_at", "").startswith(date)
            ]
            completed_tasks = [
                task for task in day_tasks if task.get("status") == "completed"
            ]

            score = len(completed_tasks) / len(day_tasks) * 100 if day_tasks else 0
            trends.append({"date": date, "score": score})

        trends.reverse()  # Oldest to newest

        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=AuditAction.READ,
            resource="analytics_trends",
        )

        return {"user_id": user_id, "trends": trends}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load trends: {str(e)}")


@router.get("/weekly-review", summary="AI-generated summary of the week")
async def weekly_review(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get weekly review data."""
    try:
        supabase = get_supabase_client()
        user_id = current_user["id"]

        # Get last week's data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Get tasks for the week
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .execute()
        )
        tasks = tasks_result.data or []

        completed_tasks = [task for task in tasks if task.get("status") == "completed"]
        missed_tasks = [
            task
            for task in tasks
            if task.get("status") == "pending"
            and task.get("due_date")
            and datetime.fromisoformat(task["due_date"].replace("Z", "+00:00"))
            < end_date
        ]

        # Calculate streak (consecutive days with completed tasks)
        streak = calculate_streak(tasks)

        review = {
            "summary": generate_weekly_summary(completed_tasks, missed_tasks, streak),
            "completed_tasks": len(completed_tasks),
            "missed_tasks": len(missed_tasks),
            "streak": streak,
            "total_tasks": len(tasks),
        }

        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=AuditAction.READ,
            resource="analytics_weekly_review",
        )

        return {"user_id": user_id, **review}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load weekly review: {str(e)}"
        )


@router.get("/productivity-patterns", summary="Best day/time insights")
async def productivity_patterns(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get productivity pattern analysis."""
    try:
        supabase = get_supabase_client()
        user_id = current_user["id"]

        # Get schedule blocks for analysis
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        schedule_blocks = schedule_result.data or []

        # Analyze patterns
        pattern = analyze_productivity_patterns(schedule_blocks)

        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=AuditAction.READ,
            resource="analytics_productivity_patterns",
        )

        return {"user_id": user_id, **pattern}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load productivity patterns: {str(e)}"
        )


# Helper functions
def calculate_productivity_score(tasks, schedule_blocks, goals):
    """Calculate overall productivity score."""
    if not tasks:
        return 0

    completed_tasks = len([task for task in tasks if task.get("status") == "completed"])
    task_completion = (completed_tasks / len(tasks)) * 100

    # Factor in schedule adherence
    schedule_adherence = 0
    if schedule_blocks:
        # Simple calculation - could be more sophisticated
        schedule_adherence = min(100, len(schedule_blocks) * 10)

    # Factor in goal progress
    goal_progress = 0
    if goals:
        goal_progress = sum(goal.get("progress", 0) for goal in goals) / len(goals)

    return int((task_completion * 0.5 + schedule_adherence * 0.3 + goal_progress * 0.2))


def calculate_streak(tasks):
    """Calculate consecutive days with completed tasks."""
    if not tasks:
        return 0

    completed_dates = set()
    for task in tasks:
        if task.get("status") == "completed" and task.get("updated_at"):
            date = task["updated_at"].split("T")[0]
            completed_dates.add(date)

    if not completed_dates:
        return 0

    # Calculate consecutive days
    dates = sorted(completed_dates)
    streak = 1
    max_streak = 1

    for i in range(1, len(dates)):
        prev_date = datetime.fromisoformat(dates[i - 1])
        curr_date = datetime.fromisoformat(dates[i])
        if (curr_date - prev_date).days == 1:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1

    return max_streak


def generate_weekly_summary(completed_tasks, missed_tasks, streak):
    """Generate AI-like weekly summary."""
    if len(completed_tasks) > len(missed_tasks):
        return f"Great week! You completed {len(completed_tasks)} tasks and maintained a {streak}-day streak."
    elif len(completed_tasks) == 0:
        return "This week was challenging. Let's focus on small wins next week."
    else:
        return f"Mixed results this week. You completed {len(completed_tasks)} tasks but missed {len(missed_tasks)}."


def analyze_productivity_patterns(schedule_blocks):
    """Analyze productivity patterns from schedule blocks."""
    if not schedule_blocks:
        return {"best_time": "morning", "best_day": "Monday", "focus_blocks": []}

    # Analyze by day of week
    day_counts = {}
    for block in schedule_blocks:
        if block.get("start_time"):
            try:
                start_time = datetime.fromisoformat(
                    block["start_time"].replace("Z", "+00:00")
                )
                day = start_time.strftime("%A")
                day_counts[day] = day_counts.get(day, 0) + 1
            except Exception:
                continue

    best_day = (
        max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "Monday"
    )

    # Analyze by time of day
    morning_blocks = 0
    afternoon_blocks = 0
    evening_blocks = 0

    for block in schedule_blocks:
        if block.get("start_time"):
            try:
                start_time = datetime.fromisoformat(
                    block["start_time"].replace("Z", "+00:00")
                )
                hour = start_time.hour
                if 6 <= hour < 12:
                    morning_blocks += 1
                elif 12 <= hour < 18:
                    afternoon_blocks += 1
                else:
                    evening_blocks += 1
            except Exception:
                continue

    if morning_blocks >= afternoon_blocks and morning_blocks >= evening_blocks:
        best_time = "morning"
    elif afternoon_blocks >= evening_blocks:
        best_time = "afternoon"
    else:
        best_time = "evening"

    # Calculate focus blocks by day
    focus_blocks = []
    for day in [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]:
        day_blocks = [
            block
            for block in schedule_blocks
            if block.get("start_time", "").startswith(day)
        ]
        total_minutes = sum(
            (
                datetime.fromisoformat(block["end_time"].replace("Z", "+00:00"))
                - datetime.fromisoformat(block["start_time"].replace("Z", "+00:00"))
            ).total_seconds()
            / 60
            for block in day_blocks
        )
        focus_blocks.append({"day": day, "minutes": int(total_minutes)})

    return {"best_time": best_time, "best_day": best_day, "focus_blocks": focus_blocks}
