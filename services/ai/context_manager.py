"""
Advanced AI Context Management with Personalization and Learning
"""

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# from services.cache import cache_service

# Minimal in-memory async cache for testing
class InMemoryAsyncCache:
    def __init__(self):
        self._store = {}
    async def get(self, key):
        return self._store.get(key)
    async def set(self, key, value, ttl=None):
        self._store[key] = value
        # TTL is ignored for in-memory test cache

cache_service = InMemoryAsyncCache()

from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context information"""

    TASK_HISTORY = "task_history"
    GOAL_PROGRESS = "goal_progress"
    HABIT_PATTERNS = "habit_patterns"
    SCHEDULE_PREFERENCES = "schedule_preferences"
    PRODUCTIVITY_PATTERNS = "productivity_patterns"
    LEARNING_PROGRESS = "learning_progress"
    MOOD_TRENDS = "mood_trends"
    INTERACTION_HISTORY = "interaction_history"


@dataclass
class UserContext:
    """Comprehensive user context for AI personalization"""

    user_id: str
    current_goals: list[dict[str, Any]]
    recent_tasks: list[dict[str, Any]]
    productivity_patterns: dict[str, Any]
    schedule_preferences: dict[str, Any]
    learning_progress: dict[str, Any]
    mood_trends: list[dict[str, Any]]
    interaction_history: list[dict[str, Any]]
    personalization_score: float
    last_updated: datetime


class AdvancedContextManager:
    """Advanced context manager with personalization and learning"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.context_cache = {}
        self.learning_weights = {
            "task_completion": 0.3,
            "schedule_adherence": 0.25,
            "goal_progress": 0.2,
            "productivity_patterns": 0.15,
            "user_feedback": 0.1,
        }

    async def build_comprehensive_context(
        self, user_id: str, context_types: list[ContextType] | None = None
    ) -> UserContext:
        """Build comprehensive user context for AI personalization"""

        if context_types is None:
            context_types = list(ContextType)

        # Check cache first
        cache_key = f"user_context:{user_id}:{hash(str(context_types))}"
        cached_context = await cache_service.get(cache_key)
        if cached_context:
            return UserContext(**cached_context)

        # Build context components
        context_data = {}

        if ContextType.CURRENT_GOALS in context_types:
            context_data["current_goals"] = await self._get_current_goals(user_id)

        if ContextType.TASK_HISTORY in context_types:
            context_data["recent_tasks"] = await self._get_recent_tasks(user_id)

        if ContextType.PRODUCTIVITY_PATTERNS in context_types:
            context_data["productivity_patterns"] = (
                await self._analyze_productivity_patterns(user_id)
            )

        if ContextType.SCHEDULE_PREFERENCES in context_types:
            context_data["schedule_preferences"] = await self._get_schedule_preferences(
                user_id
            )

        if ContextType.LEARNING_PROGRESS in context_types:
            context_data["learning_progress"] = await self._get_learning_progress(
                user_id
            )

        if ContextType.MOOD_TRENDS in context_types:
            context_data["mood_trends"] = await self._get_mood_trends(user_id)

        if ContextType.INTERACTION_HISTORY in context_types:
            context_data["interaction_history"] = await self._get_interaction_history(
                user_id
            )

        # Calculate personalization score
        personalization_score = await self._calculate_personalization_score(
            user_id, context_data
        )

        # Create context object
        user_context = UserContext(
            user_id=user_id,
            current_goals=context_data.get("current_goals", []),
            recent_tasks=context_data.get("recent_tasks", []),
            productivity_patterns=context_data.get("productivity_patterns", {}),
            schedule_preferences=context_data.get("schedule_preferences", {}),
            learning_progress=context_data.get("learning_progress", {}),
            mood_trends=context_data.get("mood_trends", []),
            interaction_history=context_data.get("interaction_history", []),
            personalization_score=personalization_score,
            last_updated=datetime.now(UTC),
        )

        # Cache the context
        await cache_service.set(cache_key, asdict(user_context), ttl=300)  # 5 minutes

        return user_context

    async def _get_current_goals(self, user_id: str) -> list[dict[str, Any]]:
        """Get user's current active goals with progress"""
        try:
            result = (
                self.supabase.table("goals")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )

            goals = []
            for goal in result.data:
                # Calculate progress
                progress = await self._calculate_goal_progress(goal["id"])
                goal["progress"] = progress
                goals.append(goal)

            return goals
        except Exception as e:
            logger.error(f"Error getting current goals: {e}")
            return []

    async def _get_recent_tasks(
        self, user_id: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get recent tasks with completion patterns"""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days)

            result = (
                self.supabase.table("tasks")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", cutoff_date.isoformat())
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            )

            return result.data
        except Exception as e:
            logger.error(f"Error getting recent tasks: {e}")
            return []

    async def _analyze_productivity_patterns(self, user_id: str) -> dict[str, Any]:
        """Analyze user's productivity patterns"""
        try:
            # Get task completion data
            result = (
                self.supabase.table("tasks")
                .select("completed_at, priority, estimated_time, actual_time")
                .eq("user_id", user_id)
                .not_.is_("completed_at", "null")
                .gte(
                    "completed_at", (datetime.now(UTC) - timedelta(days=30)).isoformat()
                )
                .execute()
            )

            patterns = {
                "peak_hours": self._find_peak_productivity_hours(result.data),
                "completion_rate": self._calculate_completion_rate(result.data),
                "priority_preferences": self._analyze_priority_patterns(result.data),
                "time_accuracy": self._analyze_time_estimates(result.data),
                "productivity_score": self._calculate_productivity_score(result.data),
            }

            return patterns
        except Exception as e:
            logger.error(f"Error analyzing productivity patterns: {e}")
            return {}

    async def _get_schedule_preferences(self, user_id: str) -> dict[str, Any]:
        """Get user's schedule preferences and patterns"""
        try:
            # Get schedule blocks
            result = (
                self.supabase.table("schedule_blocks")
                .select("*")
                .eq("user_id", user_id)
                .gte("start_time", (datetime.now(UTC) - timedelta(days=14)).isoformat())
                .execute()
            )

            preferences = {
                "preferred_work_hours": self._analyze_work_hours(result.data),
                "break_patterns": self._analyze_break_patterns(result.data),
                "focus_session_length": self._analyze_focus_sessions(result.data),
                "energy_level_patterns": self._analyze_energy_patterns(result.data),
            }

            return preferences
        except Exception as e:
            logger.error(f"Error getting schedule preferences: {e}")
            return {}

    async def _get_learning_progress(self, user_id: str) -> dict[str, Any]:
        """Get user's learning progress and patterns"""
        try:
            # Get flashcard data
            result = (
                self.supabase.table("flashcards")
                .select("*")
                .eq("user_id", user_id)
                .order("last_reviewed", desc=True)
                .limit(50)
                .execute()
            )

            progress = {
                "total_flashcards": len(result.data),
                "mastery_level": self._calculate_mastery_level(result.data),
                "learning_streak": self._calculate_learning_streak(result.data),
                "difficulty_distribution": self._analyze_difficulty_distribution(
                    result.data
                ),
                "review_patterns": self._analyze_review_patterns(result.data),
            }

            return progress
        except Exception as e:
            logger.error(f"Error getting learning progress: {e}")
            return {}

    async def _get_mood_trends(
        self, user_id: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """Get user's mood trends and patterns"""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days)

            result = (
                self.supabase.table("mood_entries")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", cutoff_date.isoformat())
                .order("created_at", desc=True)
                .execute()
            )

            return result.data
        except Exception as e:
            logger.error(f"Error getting mood trends: {e}")
            return []

    async def _get_interaction_history(self, user_id: str) -> list[dict[str, Any]]:
        """Get user's AI interaction history"""
        try:
            # This would come from a new table tracking AI interactions
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting interaction history: {e}")
            return []

    async def _calculate_personalization_score(
        self, user_id: str, context_data: dict
    ) -> float:
        """Calculate how well we can personalize for this user"""
        score = 0.0
        total_weight = 0.0

        # Score based on data availability and quality
        if context_data.get("recent_tasks"):
            score += self.learning_weights["task_completion"] * min(
                len(context_data["recent_tasks"]) / 10, 1.0
            )
            total_weight += self.learning_weights["task_completion"]

        if context_data.get("schedule_preferences"):
            score += self.learning_weights["schedule_adherence"] * 0.8
            total_weight += self.learning_weights["schedule_adherence"]

        if context_data.get("current_goals"):
            score += self.learning_weights["goal_progress"] * min(
                len(context_data["current_goals"]) / 3, 1.0
            )
            total_weight += self.learning_weights["goal_progress"]

        if context_data.get("productivity_patterns"):
            score += self.learning_weights["productivity_patterns"] * 0.9
            total_weight += self.learning_weights["productivity_patterns"]

        return score / total_weight if total_weight > 0 else 0.0

    def _find_peak_productivity_hours(self, task_data: list[dict]) -> list[int]:
        """Find hours when user is most productive"""
        hour_counts = {}
        for task in task_data:
            if task.get("completed_at"):
                hour = datetime.fromisoformat(
                    task["completed_at"].replace("Z", "+00:00")
                ).hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Return top 3 most productive hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    def _calculate_completion_rate(self, task_data: list[dict]) -> float:
        """Calculate task completion rate"""
        if not task_data:
            return 0.0

        completed = len([t for t in task_data if t.get("completed_at")])
        return completed / len(task_data)

    def _analyze_priority_patterns(self, task_data: list[dict]) -> dict[str, float]:
        """Analyze priority completion patterns"""
        priority_counts = {}
        priority_completed = {}

        for task in task_data:
            priority = task.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            if task.get("completed_at"):
                priority_completed[priority] = priority_completed.get(priority, 0) + 1

        patterns = {}
        for priority in priority_counts:
            if priority_counts[priority] > 0:
                patterns[priority] = (
                    priority_completed.get(priority, 0) / priority_counts[priority]
                )

        return patterns

    def _analyze_time_estimates(self, task_data: list[dict]) -> dict[str, float]:
        """Analyze accuracy of time estimates"""
        total_estimated = 0
        total_actual = 0
        count = 0

        for task in task_data:
            if task.get("estimated_time") and task.get("actual_time"):
                total_estimated += task["estimated_time"]
                total_actual += task["actual_time"]
                count += 1

        if count == 0:
            return {"accuracy": 0.0, "bias": 0.0}

        accuracy = 1 - abs(total_estimated - total_actual) / total_actual
        bias = (total_estimated - total_actual) / total_actual

        return {"accuracy": max(0, accuracy), "bias": bias}

    def _calculate_productivity_score(self, task_data: list[dict]) -> float:
        """Calculate overall productivity score"""
        if not task_data:
            return 0.0

        completion_rate = self._calculate_completion_rate(task_data)
        time_accuracy = self._analyze_time_estimates(task_data)["accuracy"]

        # Weighted average
        return (completion_rate * 0.7) + (time_accuracy * 0.3)

    async def _calculate_goal_progress(self, goal_id: str) -> float:
        """Calculate progress for a specific goal"""
        try:
            # Get goal tasks
            result = (
                self.supabase.table("tasks")
                .select("status")
                .eq("goal_id", goal_id)
                .execute()
            )

            if not result.data:
                return 0.0

            completed = len([t for t in result.data if t["status"] == "completed"])
            return completed / len(result.data)
        except Exception as e:
            logger.error(f"Error calculating goal progress: {e}")
            return 0.0

    def _analyze_work_hours(self, schedule_data: list[dict]) -> dict[str, Any]:
        """Analyze preferred work hours"""
        hour_counts = {}
        for block in schedule_data:
            if block.get("start_time"):
                hour = datetime.fromisoformat(
                    block["start_time"].replace("Z", "+00:00")
                ).hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if not hour_counts:
            return {"start_hour": 9, "end_hour": 17}

        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return {
            "start_hour": sorted_hours[0][0],
            "end_hour": (
                sorted_hours[-1][0] if len(sorted_hours) > 1 else sorted_hours[0][0] + 8
            ),
        }

    def _analyze_break_patterns(self, schedule_data: list[dict]) -> dict[str, Any]:
        """Analyze break patterns"""
        break_blocks = [b for b in schedule_data if b.get("focus_type") == "break"]

        if not break_blocks:
            return {"frequency": "every_2_hours", "duration": 15}

        # Calculate average break duration and frequency
        durations = []
        for block in break_blocks:
            if block.get("start_time") and block.get("end_time"):
                start = datetime.fromisoformat(
                    block["start_time"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(block["end_time"].replace("Z", "+00:00"))
                durations.append((end - start).total_seconds() / 60)

        avg_duration = sum(durations) / len(durations) if durations else 15

        return {
            "frequency": "every_2_hours",  # Simplified for now
            "duration": round(avg_duration),
        }

    def _analyze_focus_sessions(self, schedule_data: list[dict]) -> dict[str, Any]:
        """Analyze focus session patterns"""
        focus_blocks = [b for b in schedule_data if b.get("focus_type") == "deep_work"]

        if not focus_blocks:
            return {"average_length": 90, "max_length": 120}

        durations = []
        for block in focus_blocks:
            if block.get("start_time") and block.get("end_time"):
                start = datetime.fromisoformat(
                    block["start_time"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(block["end_time"].replace("Z", "+00:00"))
                durations.append((end - start).total_seconds() / 60)

        return {
            "average_length": (
                round(sum(durations) / len(durations)) if durations else 90
            ),
            "max_length": max(durations) if durations else 120,
        }

    def _analyze_energy_patterns(self, schedule_data: list[dict]) -> dict[str, Any]:
        """Analyze energy level patterns"""
        energy_counts = {}
        for block in schedule_data:
            energy = block.get("energy_level", "medium")
            energy_counts[energy] = energy_counts.get(energy, 0) + 1

        if not energy_counts:
            return {"peak_energy": "morning", "low_energy": "afternoon"}

        # Determine peak and low energy times based on energy levels
        return {
            "peak_energy": "morning",  # Simplified for now
            "low_energy": "afternoon",
        }

    def _calculate_mastery_level(self, flashcard_data: list[dict]) -> float:
        """Calculate overall mastery level from flashcards"""
        if not flashcard_data:
            return 0.0

        total_difficulty = 0
        for card in flashcard_data:
            difficulty = card.get("difficulty", 1)
            total_difficulty += difficulty

        return total_difficulty / len(flashcard_data)

    def _calculate_learning_streak(self, flashcard_data: list[dict]) -> int:
        """Calculate current learning streak"""
        if not flashcard_data:
            return 0

        # Sort by last reviewed date
        sorted_cards = sorted(
            flashcard_data, key=lambda x: x.get("last_reviewed", ""), reverse=True
        )

        streak = 0
        current_date = None

        for card in sorted_cards:
            if card.get("last_reviewed"):
                card_date = datetime.fromisoformat(
                    card["last_reviewed"].replace("Z", "+00:00")
                ).date()

                if current_date is None:
                    current_date = card_date
                    streak = 1
                elif (current_date - card_date).days == 1:
                    current_date = card_date
                    streak += 1
                else:
                    break

        return streak

    def _analyze_difficulty_distribution(
        self, flashcard_data: list[dict]
    ) -> dict[str, int]:
        """Analyze difficulty distribution of flashcards"""
        distribution = {"easy": 0, "medium": 0, "hard": 0}

        for card in flashcard_data:
            difficulty = card.get("difficulty", 1)
            if difficulty <= 2:
                distribution["easy"] += 1
            elif difficulty <= 4:
                distribution["medium"] += 1
            else:
                distribution["hard"] += 1

        return distribution

    def _analyze_review_patterns(self, flashcard_data: list[dict]) -> dict[str, Any]:
        """Analyze review patterns"""
        if not flashcard_data:
            return {"average_reviews_per_day": 0, "preferred_review_time": "morning"}

        # Calculate average reviews per day
        total_reviews = sum(card.get("review_count", 0) for card in flashcard_data)
        days_active = 30  # Assume 30 days of activity
        avg_reviews = total_reviews / days_active

        return {
            "average_reviews_per_day": round(avg_reviews, 1),
            "preferred_review_time": "morning",  # Simplified for now
        }

    async def update_user_learning(
        self, user_id: str, interaction_data: dict[str, Any]
    ):
        pass
        """Update user learning based on AI interactions"""
        try:
            # Store interaction data for future learning
            {
                "user_id": user_id,
                "interaction_type": interaction_data.get("type"),
                "interaction_data": interaction_data,
                "timestamp": datetime.utcnow().isoformat(),
                "context_snapshot": self._get_current_context_snapshot(user_id),
            }
            # TODO: Store interaction record in database for learning

            # Update learning weights based on feedback
            if interaction_data.get("feedback") == "positive":
                await self._adjust_learning_weights(user_id, "positive")
            elif interaction_data.get("feedback") == "negative":
                await self._adjust_learning_weights(user_id, "negative")

        except Exception as e:
            logger.error(f"Error updating user learning: {e}")

    async def _adjust_learning_weights(self, user_id: str, feedback_type: str):
        pass
        """Adjust learning weights based on user feedback"""
        # This would implement adaptive learning
        # For now, just log the feedback
        logger.info(f"User {user_id} provided {feedback_type} feedback")


# Global instance
context_manager = AdvancedContextManager()


def get_context_manager() -> AdvancedContextManager:
    """Get the global context manager instance"""
    return context_manager
