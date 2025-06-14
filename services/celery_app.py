from celery import Celery
from celery.signals import after_setup_logger
import logging
from typing import Any, Dict
import os
from datetime import timedelta

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Celery configuration
celery_app = Celery(
    "personal_agent",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["services.tasks"]
)

# Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "notion": {
            "exchange": "notion",
            "routing_key": "notion",
        },
        "ai": {
            "exchange": "ai",
            "routing_key": "ai",
        },
        "email": {
            "exchange": "email",
            "routing_key": "email",
        }
    },
    task_routes={
        "services.tasks.notion.*": {"queue": "notion"},
        "services.tasks.ai.*": {"queue": "ai"},
        "services.tasks.email.*": {"queue": "email"},
    },
    beat_schedule={
        "sync-notion": {
            "task": "services.tasks.notion.sync_notion_data",
            "schedule": timedelta(minutes=15),
        },
        "cleanup-old-tasks": {
            "task": "services.tasks.cleanup.cleanup_old_tasks",
            "schedule": timedelta(days=1),
        }
    }
)

@after_setup_logger.connect
def setup_loggers(logger: logging.Logger, *args: Any, **kwargs: Dict[str, Any]) -> None:
    """Configure Celery logging."""
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # File handler
    fh = logging.FileHandler("logs/celery.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    logger.setLevel(logging.INFO) 