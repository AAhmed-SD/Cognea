from celery import Task
from services.celery_app import celery_app
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from models.database import SessionLocal
from services.notion import NotionClient
from models.user import User

logger = logging.getLogger(__name__)

class NotionTask(Task):
    """Base task class for Notion operations with error handling."""
    _notion_client: Optional[NotionClient] = None
    
    @property
    def notion_client(self) -> NotionClient:
        if self._notion_client is None:
            self._notion_client = NotionClient()
        return self._notion_client
    
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
    base=NotionTask,
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    rate_limit="10/m"  # 10 tasks per minute
)
def sync_notion_data(self, user_id: str) -> Dict[str, Any]:
    """Sync user's Notion data with retries and error handling."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        # Sync tasks
        tasks = self.notion_client.get_tasks(user_id)
        # Sync pages
        pages = self.notion_client.get_pages(user_id)
        # Sync databases
        databases = self.notion_client.get_databases(user_id)
        return {
            "status": "success",
            "tasks_synced": len(tasks),
            "pages_synced": len(pages),
            "databases_synced": len(databases),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Notion sync failed for user {user_id}: {exc}")
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(
    base=NotionTask,
    bind=True,
    max_retries=2,
    default_retry_delay=60,  # 1 minute
    rate_limit="30/m"  # 30 tasks per minute
)
def push_to_notion(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Push data to Notion with retries and error handling."""
    try:
        result = self.notion_client.push_data(user_id, data)
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Notion push failed for user {user_id}: {exc}")
        self.retry(exc=exc) 