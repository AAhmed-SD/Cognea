from fastapi import BackgroundTasks
from typing import Callable, Any
import logging
import asyncio
from functools import wraps
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


def log_background_task(func: Callable) -> Callable:
    """Decorator to log background task execution and errors."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        task_id = f"{func.__name__}_{datetime.utcnow().isoformat()}"
        logger.info(f"Starting background task {task_id}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Completed background task {task_id}")
            return result
        except Exception as exc:
            logger.error(
                f"Background task {task_id} failed: {exc}",
                extra={
                    "task_id": task_id,
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    return wrapper


class BackgroundTaskManager:
    """Manager for FastAPI background tasks with error handling."""

    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Add a task to the background queue with error handling."""

        @log_background_task
        async def wrapped_task() -> None:
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            except Exception as exc:
                logger.error(
                    f"Background task failed: {exc}",
                    extra={
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "exception": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                )
                raise

        self.background_tasks.add_task(wrapped_task)

    def add_task_with_retry(
        self,
        func: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add a task with retry logic to the background queue."""

        @log_background_task
        async def wrapped_task_with_retry() -> None:
            for attempt in range(max_retries):
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
                    return
                except Exception as exc:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {exc}"
                    )
                    await asyncio.sleep(retry_delay * (attempt + 1))

        self.background_tasks.add_task(wrapped_task_with_retry)


# Example usage of AuditLogger dependency in a background task endpoint:
# from fastapi import APIRouter
# router = APIRouter()
# @router.post("/run-task", dependencies=[Depends(AuditLogger(AuditAction.CREATE, "background_task"))])
# async def run_task_endpoint(background_tasks: BackgroundTasks, request: Request):
#     ...
