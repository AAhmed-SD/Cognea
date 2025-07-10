"""
AI Migration Helper
Helps migrate existing AI services to use the hybrid AI system.
"""

import logging
from typing import Any

from .hybrid_ai_service import TaskType, get_hybrid_ai_service

logger = logging.getLogger(__name__)


class AIMigrationHelper:
    """Helper class to migrate existing AI services to hybrid system"""

    def __init__(self):
        self.hybrid_service = get_hybrid_ai_service()

    async def migrate_flashcard_generation(
        self, content: str, user_id: str, **kwargs
    ) -> dict[str, Any]:
        """Migrate flashcard generation to hybrid system"""
        try:
            response = await self.hybrid_service.generate_response(
                task_type=TaskType.FLASHCARD, prompt=content, user_id=user_id, **kwargs
            )

            return {
                "success": True,
                "flashcards": self._parse_flashcards(response.content),
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def migrate_exam_generation(
        self, topic: str, difficulty: str, user_id: str, **kwargs
    ) -> dict[str, Any]:
        """Migrate exam question generation to hybrid system"""
        try:
            prompt = f"Generate {kwargs.get('count', 5)} {difficulty} exam questions about {topic}"

            response = await self.hybrid_service.generate_response(
                task_type=TaskType.EXAM_QUESTION,
                prompt=prompt,
                user_id=user_id,
                **kwargs,
            )

            return {
                "success": True,
                "questions": self._parse_exam_questions(response.content),
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Exam generation failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def migrate_productivity_analysis(
        self, user_data: dict[str, Any], user_id: str, **kwargs
    ) -> dict[str, Any]:
        """Migrate productivity analysis to hybrid system"""
        try:
            prompt = self._build_productivity_prompt(user_data)

            response = await self.hybrid_service.generate_response(
                task_type=TaskType.PRODUCTIVITY_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                **kwargs,
            )

            return {
                "success": True,
                "analysis": response.content,
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Productivity analysis failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def migrate_task_generation(
        self, context: str, user_id: str, **kwargs
    ) -> dict[str, Any]:
        """Migrate task generation to hybrid system"""
        try:
            response = await self.hybrid_service.generate_response(
                task_type=TaskType.TASK_GENERATION,
                prompt=context,
                user_id=user_id,
                **kwargs,
            )

            return {
                "success": True,
                "tasks": self._parse_tasks(response.content),
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Task generation failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def migrate_schedule_optimization(
        self, schedule_data: dict[str, Any], user_id: str, **kwargs
    ) -> dict[str, Any]:
        """Migrate schedule optimization to hybrid system"""
        try:
            prompt = self._build_schedule_prompt(schedule_data)

            response = await self.hybrid_service.generate_response(
                task_type=TaskType.SCHEDULE_OPTIMIZATION,
                prompt=prompt,
                user_id=user_id,
                **kwargs,
            )

            return {
                "success": True,
                "optimized_schedule": self._parse_schedule(response.content),
                "model_used": response.model_used,
                "provider": response.provider,
                "cost_usd": response.cost_usd,
                "quality_score": response.quality_score,
            }

        except Exception as e:
            logger.error(f"Schedule optimization failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    async def get_cost_comparison(
        self, task_type: TaskType, prompt: str
    ) -> dict[str, Any]:
        """Get cost comparison between providers for a specific task"""
        try:
            analysis = await self.hybrid_service.get_cost_analysis(task_type, prompt)

            # Calculate potential savings
            openai_cost = analysis.get("openai_api", {}).get("estimated_cost_usd", 0)
            hybrid_cost = min(
                analysis.get("llama_self_hosted", {}).get(
                    "estimated_cost_usd", float("inf")
                ),
                analysis.get("deepseek_api", {}).get(
                    "estimated_cost_usd", float("inf")
                ),
                analysis.get("claude_api", {}).get("estimated_cost_usd", float("inf")),
            )

            savings_percentage = (
                ((openai_cost - hybrid_cost) / openai_cost * 100)
                if openai_cost > 0
                else 0
            )

            return {
                "analysis": analysis,
                "openai_cost": openai_cost,
                "hybrid_cost": hybrid_cost,
                "savings_percentage": savings_percentage,
                "recommended_provider": min(
                    analysis.items(), key=lambda x: x[1]["estimated_cost_usd"]
                )[0],
            }

        except Exception as e:
            logger.error(f"Cost comparison failed: {e}")
            return {"error": str(e)}

    def _parse_flashcards(self, content: str) -> list:
        """Parse flashcard content from AI response"""
        # Basic parsing - can be enhanced based on your format
        lines = content.strip().split("\n")
        flashcards = []

        for line in lines:
            if ":" in line or " - " in line:
                parts = line.replace(":", " - ").split(" - ", 1)
                if len(parts) == 2:
                    flashcards.append(
                        {"question": parts[0].strip(), "answer": parts[1].strip()}
                    )

        return flashcards

    def _parse_exam_questions(self, content: str) -> list:
        """Parse exam questions from AI response"""
        # Basic parsing - can be enhanced based on your format
        lines = content.strip().split("\n")
        questions = []
        current_question = None

        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                if current_question:
                    questions.append(current_question)
                current_question = {"question": line.strip(), "options": []}
            elif current_question and line.strip().startswith(("A.", "B.", "C.", "D.")):
                current_question["options"].append(line.strip())

        if current_question:
            questions.append(current_question)

        return questions

    def _parse_tasks(self, content: str) -> list:
        """Parse tasks from AI response"""
        # Basic parsing - can be enhanced based on your format
        lines = content.strip().split("\n")
        tasks = []

        for line in lines:
            if line.strip().startswith(("-", "•", "*", "1.", "2.", "3.")):
                task_text = line.strip().lstrip("-•*1234567890. ")
                if task_text:
                    tasks.append({"title": task_text, "completed": False})

        return tasks

    def _parse_schedule(self, content: str) -> dict[str, Any]:
        """Parse optimized schedule from AI response"""
        # Basic parsing - can be enhanced based on your format
        return {
            "schedule": content,
            "optimization_notes": "Generated by hybrid AI system",
        }

    def _build_productivity_prompt(self, user_data: dict[str, Any]) -> str:
        """Build productivity analysis prompt"""
        return f"""
        Analyze the following user productivity data and provide insights:
        
        User Data:
        - Tasks completed: {user_data.get('tasks_completed', 0)}
        - Study time: {user_data.get('study_time', 0)} hours
        - Goals achieved: {user_data.get('goals_achieved', 0)}
        - Productivity score: {user_data.get('productivity_score', 0)}
        
        Please provide:
        1. Key insights about productivity patterns
        2. Areas for improvement
        3. Specific recommendations
        4. Goal suggestions for next period
        """

    def _build_schedule_prompt(self, schedule_data: dict[str, Any]) -> str:
        """Build schedule optimization prompt"""
        return f"""
        Optimize the following schedule for maximum productivity:
        
        Current Schedule:
        {schedule_data.get('current_schedule', 'No schedule provided')}
        
        Constraints:
        - Available time: {schedule_data.get('available_hours', 24)} hours
        - Priority tasks: {schedule_data.get('priority_tasks', [])}
        - Study goals: {schedule_data.get('study_goals', [])}
        
        Please provide an optimized schedule that:
        1. Maximizes productivity
        2. Balances work and study
        3. Includes breaks and rest periods
        4. Prioritizes important tasks
        """


# Global instance
_migration_helper = None


def get_migration_helper() -> AIMigrationHelper:
    """Get the global migration helper instance"""
    global _migration_helper
    if _migration_helper is None:
        _migration_helper = AIMigrationHelper()
    return _migration_helper
