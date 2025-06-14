from celery import Task
from services.celery_app import celery_app
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from models.database import SessionLocal
from models.diary import DiaryEntry
from models.user import User

logger = logging.getLogger(__name__)

class CleanupTask(Task):
    """Base task class for cleanup operations with error handling."""
    
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
    base=CleanupTask,
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def cleanup_old_tasks(self) -> Dict[str, Any]:
    """Clean up old tasks and temporary data."""
    db = SessionLocal()
    try:
        # Clean up old diary entries (older than 1 year)
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        old_entries = db.query(DiaryEntry).filter(
            DiaryEntry.created_at < cutoff_date
        ).all()
        
        for entry in old_entries:
            db.delete(entry)
        
        db.commit()
        
        return {
            "status": "success",
            "entries_cleaned": len(old_entries),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(
    base=CleanupTask,
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def cleanup_inactive_users(self) -> Dict[str, Any]:
    """Clean up data for inactive users."""
    db = SessionLocal()
    try:
        # Find users inactive for more than 6 months
        cutoff_date = datetime.utcnow() - timedelta(days=180)
        inactive_users = db.query(User).filter(
            User.last_login < cutoff_date
        ).all()
        
        cleaned_users = []
        for user in inactive_users:
            # Archive user data instead of deleting
            user.is_active = False
            user.archived_at = datetime.utcnow()
            cleaned_users.append(user.id)
        
        db.commit()
        
        return {
            "status": "success",
            "users_archived": len(cleaned_users),
            "user_ids": cleaned_users,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        logger.error(f"User cleanup failed: {exc}")
        self.retry(exc=exc)
    finally:
        db.close() 