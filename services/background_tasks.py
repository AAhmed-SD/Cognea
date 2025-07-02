from fastapi import BackgroundTasks
from typing import Callable, Any, Dict
import logging
import asyncio
from functools import wraps
import traceback
from datetime import datetime
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class TaskErrorType(Enum):
    """Categorization of background task errors."""

    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    PROGRAMMING_ERROR = "programming_error"
    UNKNOWN_ERROR = "unknown_error"


class TaskStatus(Enum):
    """Status of background tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


def categorize_task_error(error: Exception) -> Dict[str, Any]:
    """Categorize background task errors for better handling."""
    error_message = str(error)

    # Network and connection errors
    if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return {
            "type": TaskErrorType.NETWORK_ERROR,
            "retryable": True,
            "retry_delay_multiplier": 2.0,
            "max_retries": 5,
        }

    # Timeout errors
    if "timeout" in error_message.lower() or "timed out" in error_message.lower():
        return {
            "type": TaskErrorType.TIMEOUT_ERROR,
            "retryable": True,
            "retry_delay_multiplier": 1.5,
            "max_retries": 3,
        }

    # Validation errors
    if (
        isinstance(error, (ValueError, TypeError))
        or "validation" in error_message.lower()
    ):
        return {
            "type": TaskErrorType.VALIDATION_ERROR,
            "retryable": False,
            "max_retries": 0,
        }

    # Permission errors
    if "permission" in error_message.lower() or "unauthorized" in error_message.lower():
        return {
            "type": TaskErrorType.PERMISSION_ERROR,
            "retryable": False,
            "max_retries": 0,
        }

    # Resource errors
    if any(
        keyword in error_message.lower()
        for keyword in ["memory", "disk", "resource", "quota"]
    ):
        return {
            "type": TaskErrorType.RESOURCE_ERROR,
            "retryable": True,
            "retry_delay_multiplier": 3.0,
            "max_retries": 2,
        }

    # External service errors
    if any(
        keyword in error_message.lower()
        for keyword in ["api", "service", "external", "third-party"]
    ):
        return {
            "type": TaskErrorType.EXTERNAL_SERVICE_ERROR,
            "retryable": True,
            "retry_delay_multiplier": 2.0,
            "max_retries": 4,
        }

    # Programming errors
    if isinstance(error, (AttributeError, KeyError, IndexError, ImportError)):
        return {
            "type": TaskErrorType.PROGRAMMING_ERROR,
            "retryable": False,
            "max_retries": 0,
        }

    # Unknown errors
    return {
        "type": TaskErrorType.UNKNOWN_ERROR,
        "retryable": True,
        "retry_delay_multiplier": 1.0,
        "max_retries": 3,
    }


class TaskMetrics:
    """Metrics tracking for background tasks."""

    def __init__(self):
        self.tasks_started = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tasks_retried = 0
        self.total_processing_time = 0.0
        self.error_counts = {error_type.value: 0 for error_type in TaskErrorType}
        self.task_type_counts = {}
        self.last_activity = None

    def record_task_start(self, task_type: str):
        """Record task start."""
        self.tasks_started += 1
        self.task_type_counts[task_type] = self.task_type_counts.get(task_type, 0) + 1
        self.last_activity = datetime.utcnow().isoformat()

    def record_task_completion(self, processing_time: float):
        """Record successful task completion."""
        self.tasks_completed += 1
        self.total_processing_time += processing_time
        self.last_activity = datetime.utcnow().isoformat()

    def record_task_failure(self, error_type: TaskErrorType, processing_time: float):
        """Record task failure."""
        self.tasks_failed += 1
        self.error_counts[error_type.value] += 1
        self.total_processing_time += processing_time
        self.last_activity = datetime.utcnow().isoformat()

    def record_task_retry(self):
        """Record task retry."""
        self.tasks_retried += 1
        self.last_activity = datetime.utcnow().isoformat()

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        total_tasks = self.tasks_completed + self.tasks_failed
        success_rate = 0
        avg_processing_time = 0

        if total_tasks > 0:
            success_rate = (self.tasks_completed / total_tasks) * 100
            avg_processing_time = self.total_processing_time / total_tasks

        return {
            "tasks_started": self.tasks_started,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_retried": self.tasks_retried,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "error_distribution": self.error_counts,
            "task_type_distribution": self.task_type_counts,
            "last_activity": self.last_activity,
        }


# Global metrics instance
task_metrics = TaskMetrics()


def log_background_task(func: Callable) -> Callable:
    """Enhanced decorator to log background task execution and errors."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        task_id = f"{func.__name__}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        # Record task start
        task_metrics.record_task_start(func.__name__)

        logger.info(f"Starting background task {task_id} ({func.__name__})")

        try:
            result = await func(*args, **kwargs)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            task_metrics.record_task_completion(processing_time)

            logger.info(
                f"Completed background task {task_id} in {processing_time:.2f}s"
            )
            return result

        except Exception as exc:
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Categorize error
            error_info = categorize_task_error(exc)
            task_metrics.record_task_failure(error_info["type"], processing_time)

            logger.error(
                f"Background task {task_id} failed: {exc}",
                extra={
                    "task_id": task_id,
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": str(exc),
                    "error_type": error_info["type"].value,
                    "retryable": error_info["retryable"],
                    "processing_time": processing_time,
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    return wrapper


class BackgroundTaskManager:
    """Enhanced manager for FastAPI background tasks with error handling and monitoring."""

    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> str:
        """Add a task to the background queue with enhanced error handling."""
        task_id = f"{func.__name__}_{uuid.uuid4().hex[:8]}"

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
                        "task_id": task_id,
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "exception": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                )
                raise

        self.background_tasks.add_task(wrapped_task)
        return task_id

    def add_task_with_retry(
        self,
        func: Callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Add a task with enhanced retry logic to the background queue."""
        task_id = f"{func.__name__}_{uuid.uuid4().hex[:8]}"

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
                    # Categorize error for retry decision
                    error_info = categorize_task_error(exc)

                    if (
                        not error_info["retryable"]
                        or attempt >= error_info["max_retries"] - 1
                    ):
                        raise

                    # Calculate retry delay with exponential backoff
                    delay = retry_delay * (
                        error_info["retry_delay_multiplier"] ** attempt
                    )
                    task_metrics.record_task_retry()

                    logger.warning(
                        f"Retry {attempt + 1}/{error_info['max_retries']} for {func.__name__} "
                        f"({error_info['type'].value}): {exc}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)

        self.background_tasks.add_task(wrapped_task_with_retry)
        return task_id

    def add_task_with_timeout(
        self,
        func: Callable,
        timeout: float = 300.0,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Add a task with timeout to the background queue."""
        task_id = f"{func.__name__}_{uuid.uuid4().hex[:8]}"

        @log_background_task
        async def wrapped_task_with_timeout() -> None:
            try:
                if asyncio.iscoroutinefunction(func):
                    await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    # Run sync function in thread pool with timeout
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, func, *args, **kwargs),
                        timeout=timeout,
                    )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Task {func.__name__} timed out after {timeout}s")
            except Exception:
                raise

        self.background_tasks.add_task(wrapped_task_with_timeout)
        return task_id

    def get_metrics(self) -> Dict[str, Any]:
        """Get background task metrics."""
        return task_metrics.get_summary()

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of background task system."""
        metrics = task_metrics.get_summary()

        # Calculate health indicators
        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]
        error_rate = 0
        if total_tasks > 0:
            error_rate = (metrics["tasks_failed"] / total_tasks) * 100

        # Determine overall health
        if error_rate > 50:
            health_status = "unhealthy"
        elif error_rate > 20:
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "status": health_status,
            "error_rate": error_rate,
            "success_rate": metrics["success_rate"],
            "active_tasks": len(self.active_tasks),
            "last_activity": metrics["last_activity"],
            "metrics": metrics,
        }


# Example usage of AuditLogger dependency in a background task endpoint:
# from fastapi import APIRouter
# router = APIRouter()
# @router.post("/run-task", dependencies=[Depends(AuditLogger(AuditAction.CREATE, "background_task"))])
# async def run_task_endpoint(background_tasks: BackgroundTasks, request: Request):
#     ...
