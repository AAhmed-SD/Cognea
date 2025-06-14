from celery import Task
from services.celery_app import celery_app
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from models.database import SessionLocal
from services.openai_integration import OpenAIClient
from models.user import User

logger = logging.getLogger(__name__)

class AITask(Task):
    """Base task class for AI operations with error handling."""
    _openai_client: Optional[OpenAIClient] = None
    
    @property
    def openai_client(self) -> OpenAIClient:
        if self._openai_client is None:
            self._openai_client = OpenAIClient()
        return self._openai_client
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task failures."""
        logger.error(
            f"Task {task_id} failed: {exc}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "traceback": einfo.traceback
            }
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(
    base=AITask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    rate_limit="20/m"  # 20 tasks per minute
)
def generate_daily_brief(self, user_id: str) -> Dict[str, Any]:
    """Generate daily brief with retries and error handling."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        brief = self.openai_client.generate_daily_brief(user_id)
        return {
            "status": "success",
            "brief": brief,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Daily brief generation failed for user {user_id}: {exc}")
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(
    base=AITask,
    bind=True,
    max_retries=2,
    default_retry_delay=30,  # 30 seconds
    rate_limit="30/m"  # 30 tasks per minute
)
def generate_flashcards(self, user_id: str, topic: str) -> Dict[str, Any]:
    """Generate flashcards with retries and error handling."""
    try:
        flashcards = self.openai_client.generate_flashcards(topic)
        return {
            "status": "success",
            "flashcards": flashcards,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Flashcard generation failed for user {user_id}, topic {topic}: {exc}")
        self.retry(exc=exc)

@celery_app.task(
    base=AITask,
    bind=True,
    max_retries=2,
    default_retry_delay=30,  # 30 seconds
    rate_limit="30/m"  # 30 tasks per minute
)
def analyze_mood(self, user_id: str, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze mood patterns with retries and error handling."""
    try:
        analysis = self.openai_client.analyze_mood_patterns(entries)
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Mood analysis failed for user {user_id}: {exc}")
        self.retry(exc=exc) 