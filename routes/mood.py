"""
Mood Tracking Routes with Enhanced Caching and Performance Monitoring
- Mood tracking and analysis
- Enhanced caching
- Performance monitoring
- AI-powered insights
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.ai.openai_service import get_openai_service
from services.auth import get_current_user
from services.background_workers import background_task, background_worker
from services.performance_monitor import monitor_performance
from services.redis_cache import enhanced_cache, enhanced_cached
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


class MoodEntry(BaseModel):
    mood_score: int  # 1-10 scale
    mood_description: str | None = None
    activities: list[str] | None = None
    notes: str | None = None
    timestamp: datetime | None = None


class MoodAnalysisRequest(BaseModel):
    date_range: str = "7d"  # 1d, 7d, 30d, 90d
    include_activities: bool = True
    include_correlations: bool = True


@router.post("/track")
@monitor_performance("mood_tracking")
async def track_mood(
    mood_entry: MoodEntry,
    current_user: dict = Depends(get_current_user),
):
    """Track a mood entry"""
    try:
        user_id = current_user["id"]

        # Set timestamp if not provided
        if not mood_entry.timestamp:
            mood_entry.timestamp = datetime.utcnow()

        # Store mood entry
        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .insert(
                {
                    "user_id": user_id,
                    "mood_score": mood_entry.mood_score,
                    "mood_description": mood_entry.mood_description,
                    "activities": mood_entry.activities or [],
                    "notes": mood_entry.notes,
                    "timestamp": mood_entry.timestamp.isoformat(),
                    "created_at": "now()",
                }
            )
            .execute()
        )

        # Invalidate mood cache
        await enhanced_cache.clear_pattern(f"mood:*:{user_id}:*")

        # Enqueue mood analysis task
        await background_worker.enqueue_task(
            "mood_analysis",
            user_id,
            {"trigger": "new_entry", "mood_score": mood_entry.mood_score},
            priority="low",
        )

        return {"success": True, "mood_entry": result.data[0] if result.data else None}

    except Exception as e:
        logger.error(f"Error tracking mood: {e}")
        raise HTTPException(status_code=500, detail="Failed to track mood")


@router.get("/entries")
@monitor_performance("mood_entries")
@enhanced_cached("mood", ttl=900)  # Cache for 15 minutes
async def get_mood_entries(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """Get mood entries for a user"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"entries:{user_id}:{days}"
        cached_entries = await enhanced_cache.get("mood", cache_key)

        if cached_entries:
            return cached_entries

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get mood entries
        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .order("timestamp", desc=True)
            .execute()
        )

        entries = result.data

        # Cache the result
        await enhanced_cache.set("mood", entries, 900, cache_key)

        return entries

    except Exception as e:
        logger.error(f"Error getting mood entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mood entries")


@router.get("/summary")
@monitor_performance("mood_summary")
@enhanced_cached("mood", ttl=1800)  # Cache for 30 minutes
async def get_mood_summary(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """Get mood summary and statistics"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"summary:{user_id}:{days}"
        cached_summary = await enhanced_cache.get("mood", cache_key)

        if cached_summary:
            return cached_summary

        # Get mood entries
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .execute()
        )

        entries = result.data

        # Calculate summary statistics
        if not entries:
            summary = {
                "total_entries": 0,
                "average_mood": 0,
                "mood_trend": "stable",
                "best_day": None,
                "worst_day": None,
                "most_common_activities": [],
            }
        else:
            mood_scores = [entry["mood_score"] for entry in entries]
            average_mood = sum(mood_scores) / len(mood_scores)

            # Calculate trend
            if len(entries) >= 2:
                recent_avg = sum(mood_scores[: len(mood_scores) // 2]) / (
                    len(mood_scores) // 2
                )
                older_avg = sum(mood_scores[len(mood_scores) // 2 :]) / (
                    len(mood_scores) // 2
                )
                if recent_avg > older_avg + 0.5:
                    trend = "improving"
                elif recent_avg < older_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # Find best and worst days
            best_entry = max(entries, key=lambda x: x["mood_score"])
            worst_entry = min(entries, key=lambda x: x["mood_score"])

            # Get most common activities
            all_activities = []
            for entry in entries:
                if entry.get("activities"):
                    all_activities.extend(entry["activities"])

            from collections import Counter

            activity_counts = Counter(all_activities)
            most_common_activities = [
                activity for activity, count in activity_counts.most_common(5)
            ]

            summary = {
                "total_entries": len(entries),
                "average_mood": round(average_mood, 2),
                "mood_trend": trend,
                "best_day": {
                    "date": best_entry["timestamp"],
                    "score": best_entry["mood_score"],
                    "description": best_entry.get("mood_description"),
                },
                "worst_day": {
                    "date": worst_entry["timestamp"],
                    "score": worst_entry["mood_score"],
                    "description": worst_entry.get("mood_description"),
                },
                "most_common_activities": most_common_activities,
            }

        # Cache the result
        await enhanced_cache.set("mood", summary, 1800, cache_key)

        return summary

    except Exception as e:
        logger.error(f"Error getting mood summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mood summary")


@router.post("/analysis")
@monitor_performance("mood_analysis")
@enhanced_cached("mood", ttl=3600)  # Cache for 1 hour
async def get_mood_analysis(
    request: MoodAnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get AI-powered mood analysis"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"analysis:{user_id}:{request.date_range}:{request.include_activities}:{request.include_correlations}"
        cached_analysis = await enhanced_cache.get("mood", cache_key)

        if cached_analysis:
            return cached_analysis

        # Calculate date range
        end_date = datetime.utcnow()
        if request.date_range == "1d":
            start_date = end_date - timedelta(days=1)
        elif request.date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif request.date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif request.date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)

        # Get mood entries
        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .order("timestamp")
            .execute()
        )

        entries = result.data

        if not entries:
            return {
                "message": "No mood data available for analysis",
                "period": request.date_range,
                "insights": [],
            }

        # Generate AI analysis
        analysis = await _generate_mood_analysis(entries, request)

        # Cache the result
        await enhanced_cache.set("mood", analysis, 3600, cache_key)

        return analysis

    except Exception as e:
        logger.error(f"Error generating mood analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate mood analysis")


@router.get("/correlations")
@monitor_performance("mood_correlations")
@enhanced_cached("mood", ttl=7200)  # Cache for 2 hours
async def get_mood_correlations(
    current_user: dict = Depends(get_current_user),
):
    """Get mood correlations with activities and other factors"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"correlations:{user_id}"
        cached_correlations = await enhanced_cache.get("mood", cache_key)

        if cached_correlations:
            return cached_correlations

        # Get mood entries with activities
        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .not_.is_("activities", "null")
            .execute()
        )

        entries = result.data

        if not entries:
            return {
                "message": "No activity data available for correlation analysis",
                "correlations": [],
            }

        # Calculate correlations
        correlations = await _calculate_mood_correlations(entries)

        # Cache the result
        await enhanced_cache.set("mood", correlations, 7200, cache_key)

        return correlations

    except Exception as e:
        logger.error(f"Error calculating mood correlations: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate correlations")


@router.get("/trends")
@monitor_performance("mood_trends")
@enhanced_cached("mood", ttl=1800)  # Cache for 30 minutes
async def get_mood_trends(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """Get mood trends over time"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"trends:{user_id}:{days}"
        cached_trends = await enhanced_cache.get("mood", cache_key)

        if cached_trends:
            return cached_trends

        # Get mood entries
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .order("timestamp")
            .execute()
        )

        entries = result.data

        # Calculate trends
        trends = await _calculate_mood_trends(entries)

        # Cache the result
        await enhanced_cache.set("mood", trends, 1800, cache_key)

        return trends

    except Exception as e:
        logger.error(f"Error calculating mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate trends")


@router.post("/insights")
@monitor_performance("mood_insights")
@enhanced_cached("mood", ttl=3600)  # Cache for 1 hour
async def get_mood_insights(
    current_user: dict = Depends(get_current_user),
):
    """Get AI-powered mood insights and recommendations"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cache_key = f"insights:{user_id}"
        cached_insights = await enhanced_cache.get("mood", cache_key)

        if cached_insights:
            return cached_insights

        # Get recent mood data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .order("timestamp", desc=True)
            .limit(50)
            .execute()
        )

        entries = result.data

        if not entries:
            return {
                "message": "No mood data available for insights",
                "insights": [],
                "recommendations": [],
            }

        # Generate insights
        insights = await _generate_mood_insights(entries)

        # Cache the result
        await enhanced_cache.set("mood", insights, 3600, cache_key)

        return insights

    except Exception as e:
        logger.error(f"Error generating mood insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")


@router.post("/cache/clear")
async def clear_mood_cache(current_user: dict = Depends(get_current_user)):
    """Clear mood cache for current user"""
    try:
        user_id = current_user["id"]

        # Clear all mood cache for this user
        pattern = f"mood:*:{user_id}:*"
        deleted = await enhanced_cache.clear_pattern(pattern)

        return {"message": f"Cleared {deleted} mood cache entries", "user_id": user_id}

    except Exception as e:
        logger.error(f"Error clearing mood cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# Helper functions
async def _generate_mood_analysis(
    entries: list[dict], request: MoodAnalysisRequest
) -> dict[str, Any]:
    """Generate AI-powered mood analysis"""
    try:
        # Prepare data for analysis
        mood_data = []
        for entry in entries:
            mood_data.append(
                {
                    "date": entry["timestamp"],
                    "score": entry["mood_score"],
                    "description": entry.get("mood_description", ""),
                    "activities": entry.get("activities", []),
                }
            )

        # Generate AI prompt
        prompt = f"""
        Analyze the following mood data and provide insights:
        
        Mood Data: {mood_data}
        Include Activities: {request.include_activities}
        Include Correlations: {request.include_correlations}
        
        Provide a comprehensive analysis including:
        1. Overall mood patterns and trends
        2. Factors that may influence mood
        3. Recommendations for mood improvement
        4. Notable observations
        
        Format the response as JSON with sections for patterns, factors, recommendations, and observations.
        """

        openai_service = get_openai_service()
        response = await openai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            user_id="system",
            use_functions=False,
            max_tokens=800,
        )

        # Parse response (simplified for now)
        analysis = getattr(response, "content", "Mood analysis")
        return {
            "period": request.date_range,
            "total_entries": len(entries),
            "analysis": analysis,
            "patterns": ["Pattern 1", "Pattern 2"],
            "factors": ["Factor 1", "Factor 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "observations": ["Observation 1", "Observation 2"],
        }

    except Exception as e:
        logger.error(f"Error generating mood analysis: {e}")
        return {
            "period": request.date_range,
            "total_entries": len(entries),
            "analysis": "Unable to generate analysis",
            "patterns": [],
            "factors": [],
            "recommendations": [],
            "observations": [],
        }


async def _calculate_mood_correlations(entries: list[dict]) -> dict[str, Any]:
    """Calculate mood correlations with activities"""
    try:
        # Group entries by activity
        activity_moods = {}
        for entry in entries:
            if entry.get("activities"):
                for activity in entry["activities"]:
                    if activity not in activity_moods:
                        activity_moods[activity] = []
                    activity_moods[activity].append(entry["mood_score"])

        # Calculate average mood for each activity
        correlations = []
        for activity, scores in activity_moods.items():
            if len(scores) >= 3:  # Only include activities with sufficient data
                avg_mood = sum(scores) / len(scores)
                correlations.append(
                    {
                        "activity": activity,
                        "average_mood": round(avg_mood, 2),
                        "frequency": len(scores),
                        "correlation_strength": (
                            "positive"
                            if avg_mood > 6
                            else "negative" if avg_mood < 4 else "neutral"
                        ),
                    }
                )

        # Sort by average mood
        correlations.sort(key=lambda x: x["average_mood"], reverse=True)

        return {
            "correlations": correlations,
            "total_activities": len(correlations),
            "most_positive_activity": (
                correlations[0]["activity"] if correlations else None
            ),
            "most_negative_activity": (
                correlations[-1]["activity"] if correlations else None
            ),
        }

    except Exception as e:
        logger.error(f"Error calculating mood correlations: {e}")
        return {"correlations": [], "total_activities": 0}


async def _calculate_mood_trends(entries: list[dict]) -> dict[str, Any]:
    """Calculate mood trends over time"""
    try:
        if not entries:
            return {"trends": [], "overall_trend": "stable"}

        # Group by day and calculate daily averages
        daily_moods = {}
        for entry in entries:
            date = entry["timestamp"][:10]  # Get date part
            if date not in daily_moods:
                daily_moods[date] = []
            daily_moods[date].append(entry["mood_score"])

        # Calculate daily averages
        trends = []
        for date, scores in sorted(daily_moods.items()):
            avg_mood = sum(scores) / len(scores)
            trends.append(
                {
                    "date": date,
                    "average_mood": round(avg_mood, 2),
                    "entries_count": len(scores),
                }
            )

        # Calculate overall trend
        if len(trends) >= 2:
            recent_avg = sum(t["average_mood"] for t in trends[: len(trends) // 2]) / (
                len(trends) // 2
            )
            older_avg = sum(t["average_mood"] for t in trends[len(trends) // 2 :]) / (
                len(trends) // 2
            )
            if recent_avg > older_avg + 0.5:
                overall_trend = "improving"
            elif recent_avg < older_avg - 0.5:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "stable"

        return {
            "trends": trends,
            "overall_trend": overall_trend,
            "total_days": len(trends),
        }

    except Exception as e:
        logger.error(f"Error calculating mood trends: {e}")
        return {"trends": [], "overall_trend": "stable"}


async def _generate_mood_insights(entries: list[dict]) -> dict[str, Any]:
    """Generate AI-powered mood insights"""
    try:
        # Prepare data for insights
        recent_entries = entries[:20]  # Last 20 entries

        prompt = f"""
        Based on the following recent mood entries, provide insights and recommendations:
        
        Recent Mood Entries: {recent_entries}
        
        Provide:
        1. Key insights about mood patterns
        2. Specific recommendations for mood improvement
        3. Activities that seem to positively/negatively affect mood
        4. Suggestions for maintaining good mood
        
        Format as JSON with sections for insights, recommendations, activities, and suggestions.
        """

        openai_service = get_openai_service()
        response = await openai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            user_id="system",
            use_functions=False,
            max_tokens=600,
        )

        # Parse response (simplified for now)
        analysis = getattr(response, "content", "Mood insights analysis")
        return {
            "insights": ["Insight 1", "Insight 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "positive_activities": ["Activity 1", "Activity 2"],
            "negative_activities": ["Activity 3"],
            "suggestions": ["Suggestion 1", "Suggestion 2"],
            "analysis": analysis,
        }

    except Exception as e:
        logger.error(f"Error generating mood insights: {e}")
        return {
            "insights": [],
            "recommendations": [],
            "positive_activities": [],
            "negative_activities": [],
            "suggestions": [],
            "analysis": "Unable to generate insights",
        }


# Background task for mood analysis
@background_task(name="mood_analysis", priority="low")
async def mood_analysis_task(user_id: str, config: dict[str, Any]):
    pass
    """Background task for mood analysis"""
    try:
        logger.info(f"Starting mood analysis for user {user_id}")

        # Get recent mood entries
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        supabase = get_supabase_client()
        result = (
            await supabase.table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .gte("timestamp", start_date.isoformat())
            .lte("timestamp", end_date.isoformat())
            .execute()
        )

        entries = result.data

        if entries:
            # Generate analysis
            analysis = await _generate_mood_analysis(entries, MoodAnalysisRequest())

            # Store analysis result
            await supabase.table("mood_analyses").insert(
                {
                    "user_id": user_id,
                    "analysis": analysis,
                    "trigger": config.get("trigger", "scheduled"),
                    "created_at": "now()",
                }
            ).execute()

        logger.info(f"Completed mood analysis for user {user_id}")
        return {"status": "completed"}

    except Exception as e:
        logger.error(f"Error in mood analysis task: {e}")
        raise
