"""
Smart Scheduler Service
Specialized AI-powered scheduling for student study planning with memory tracking.
"""

import json
import logging
from datetime import datetime
from typing import Any

from .hybrid_ai_service import TaskType, get_hybrid_ai_service

logger = logging.getLogger(__name__)


class SmartScheduler:
    """
    AI-powered smart scheduler for personalized study planning
    """

    def __init__(self):
        self.hybrid_service = get_hybrid_ai_service()

    async def generate_study_schedule(
        self,
        user_id: str,
        exam_dates: list[dict[str, Any]],
        flashcard_performance: dict[str, Any],
        available_time: dict[str, int],
        study_preferences: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a personalized study schedule based on:
        - Exam dates and topics
        - Flashcard performance history
        - Available study time
        - User preferences
        """

        # Build comprehensive prompt for AI
        prompt = self._build_schedule_prompt(
            exam_dates=exam_dates,
            flashcard_performance=flashcard_performance,
            available_time=available_time,
            study_preferences=study_preferences,
        )

        try:
            response = await self.hybrid_service.generate_response(
                task_type=TaskType.SMART_SCHEDULING,
                prompt=prompt,
                user_id=user_id,
                max_tokens=4000,  # Longer response for detailed scheduling
                temperature=0.3,  # Lower temperature for more consistent planning
            )

            # Parse the AI response into structured schedule
            schedule = self._parse_schedule_response(response.content)

            return {
                "success": True,
                "schedule": schedule,
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Smart scheduling failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def analyze_memory_patterns(
        self,
        user_id: str,
        flashcard_history: list[dict[str, Any]],
        study_sessions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze memory retention patterns and learning effectiveness
        """

        prompt = self._build_memory_analysis_prompt(
            flashcard_history=flashcard_history, study_sessions=study_sessions
        )

        try:
            response = await self.hybrid_service.generate_response(
                task_type=TaskType.MEMORY_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                max_tokens=2000,
                temperature=0.4,
            )

            analysis = self._parse_memory_analysis(response.content)

            return {
                "success": True,
                "analysis": analysis,
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Memory analysis failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def generate_revision_plan(
        self,
        user_id: str,
        exam_date: datetime,
        topics: list[str],
        current_progress: dict[str, float],
        available_days: int,
    ) -> dict[str, Any]:
        """
        Generate a focused revision plan for a specific exam
        """

        prompt = self._build_revision_prompt(
            exam_date=exam_date,
            topics=topics,
            current_progress=current_progress,
            available_days=available_days,
        )

        try:
            response = await self.hybrid_service.generate_response(
                task_type=TaskType.REVISION_PLANNING,
                prompt=prompt,
                user_id=user_id,
                max_tokens=3000,
                temperature=0.3,
            )

            revision_plan = self._parse_revision_plan(response.content)

            return {
                "success": True,
                "revision_plan": revision_plan,
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Revision planning failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    def _build_schedule_prompt(
        self,
        exam_dates: list[dict[str, Any]],
        flashcard_performance: dict[str, Any],
        available_time: dict[str, int],
        study_preferences: dict[str, Any],
    ) -> str:
        """Build comprehensive prompt for smart scheduling"""

        return f"""
        You are an expert study planner. Create a personalized study schedule for a student based on the following information:

        EXAM DATES:
        {json.dumps(exam_dates, indent=2)}

        FLASHCARD PERFORMANCE HISTORY:
        {json.dumps(flashcard_performance, indent=2)}

        AVAILABLE STUDY TIME (hours per day):
        {json.dumps(available_time, indent=2)}

        STUDY PREFERENCES:
        {json.dumps(study_preferences, indent=2)}

        Create a detailed study schedule that:
        1. Prioritizes weak topics based on flashcard performance
        2. Spreads revision evenly across available time
        3. Focuses more time on topics closer to exam dates
        4. Includes spaced repetition for better retention
        5. Adapts to the student's learning preferences
        6. Provides specific daily study goals and time allocations

        Return the schedule in this JSON format:
        {{
            "daily_schedule": [
                {{
                    "date": "YYYY-MM-DD",
                    "topics": ["topic1", "topic2"],
                    "flashcards_to_review": ["flashcard_id1", "flashcard_id2"],
                    "new_flashcards": ["flashcard_id3"],
                    "study_time_minutes": 120,
                    "goals": ["goal1", "goal2"],
                    "priority": "high/medium/low"
                }}
            ],
            "weekly_overview": {{
                "total_study_time": 840,
                "topics_covered": ["topic1", "topic2"],
                "weak_areas_focus": ["weak_topic1"],
                "exam_preparation_progress": 0.65
            }},
            "recommendations": [
                "Focus more on organic chemistry - 30% below target",
                "Review calculus daily - strong performance, maintain momentum"
            ]
        }}
        """

    def _build_memory_analysis_prompt(
        self,
        flashcard_history: list[dict[str, Any]],
        study_sessions: list[dict[str, Any]],
    ) -> str:
        """Build prompt for memory pattern analysis"""

        return f"""
        Analyze the student's learning patterns and memory retention based on:

        FLASHCARD HISTORY:
        {json.dumps(flashcard_history, indent=2)}

        STUDY SESSIONS:
        {json.dumps(study_sessions, indent=2)}

        Provide insights on:
        1. Which topics are consistently difficult
        2. Optimal study session length and frequency
        3. Memory retention patterns over time
        4. Best times of day for studying
        5. Recommended spaced repetition intervals
        6. Learning style indicators

        Return analysis in JSON format:
        {{
            "difficult_topics": ["topic1", "topic2"],
            "optimal_session_length": 45,
            "optimal_frequency": "daily",
            "retention_patterns": {{
                "short_term": 0.85,
                "long_term": 0.72
            }},
            "best_study_times": ["morning", "evening"],
            "spaced_repetition_intervals": [1, 3, 7, 14, 30],
            "learning_style": "visual/auditory/kinesthetic",
            "recommendations": ["rec1", "rec2"]
        }}
        """

    def _build_revision_prompt(
        self,
        exam_date: datetime,
        topics: list[str],
        current_progress: dict[str, float],
        available_days: int,
    ) -> str:
        """Build prompt for exam-specific revision planning"""

        return f"""
        Create a focused revision plan for an exam on {exam_date.strftime('%Y-%m-%d')} ({available_days} days away).

        TOPICS TO COVER:
        {json.dumps(topics, indent=2)}

        CURRENT PROGRESS (0-1 scale):
        {json.dumps(current_progress, indent=2)}

        Create a detailed revision plan that:
        1. Prioritizes topics with lowest current progress
        2. Allocates more time to complex topics
        3. Includes practice tests and mock exams
        4. Provides specific daily revision goals
        5. Includes confidence-building activities

        Return plan in JSON format:
        {{
            "revision_schedule": [
                {{
                    "day": 1,
                    "topics": ["topic1", "topic2"],
                    "activities": ["flashcards", "practice_questions"],
                    "time_allocation": {{
                        "topic1": 60,
                        "topic2": 45
                    }},
                    "goals": ["goal1", "goal2"]
                }}
            ],
            "mock_exam_schedule": [
                {{
                    "day": 5,
                    "topics": ["all"],
                    "duration_minutes": 120,
                    "purpose": "progress_check"
                }}
            ],
            "confidence_metrics": {{
                "target_confidence": 0.85,
                "current_confidence": 0.65
            }}
        }}
        """

    def _parse_schedule_response(self, content: str) -> dict[str, Any]:
        """Parse AI response into structured schedule"""
        try:
            # Try to extract JSON from the response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                # Try to find JSON in the response
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Failed to parse schedule response: {e}")
            # Return a basic structure if parsing fails
            return {
                "daily_schedule": [],
                "weekly_overview": {},
                "recommendations": ["Schedule parsing failed - please try again"],
            }

    def _parse_memory_analysis(self, content: str) -> dict[str, Any]:
        """Parse memory analysis response"""
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Failed to parse memory analysis: {e}")
            return {
                "difficult_topics": [],
                "recommendations": ["Analysis parsing failed"],
            }

    def _parse_revision_plan(self, content: str) -> dict[str, Any]:
        """Parse revision plan response"""
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Failed to parse revision plan: {e}")
            return {
                "revision_schedule": [],
                "recommendations": ["Revision plan parsing failed"],
            }


# Global instance
_smart_scheduler = None


def get_smart_scheduler() -> SmartScheduler:
    """Get the global smart scheduler instance"""
    global _smart_scheduler
    if _smart_scheduler is None:
        _smart_scheduler = SmartScheduler()
    return _smart_scheduler
