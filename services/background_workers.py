"""
Async Background Worker System
- Task queues with Redis backend
- Job scheduling with cron-like syntax
- Worker pool management
- Task monitoring and metrics
- Error handling and retries
- Distributed task processing
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
from functools import wraps
import redis.asyncio as redis
from croniter import croniter
import traceback

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskErrorType(Enum):
    """Categorization of task errors for better handling."""

    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    PROGRAMMING_ERROR = "programming_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class TaskError:
    """Structured error information for tasks."""

    type: TaskErrorType
    message: str
    details: Optional[Dict[str, Any]] = None
    retryable: bool = True
    retry_delay_multiplier: float = 1.0
    max_retries: int = 3


def categorize_task_error(error: Exception) -> TaskError:
    """Categorize task errors for better retry strategies."""
    error_message = str(error)

    # Network and connection errors
    if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return TaskError(
            type=TaskErrorType.NETWORK_ERROR,
            message=error_message,
            retryable=True,
            retry_delay_multiplier=2.0,  # Exponential backoff
            max_retries=5,
        )

    # Timeout errors
    if "timeout" in error_message.lower() or "timed out" in error_message.lower():
        return TaskError(
            type=TaskErrorType.TIMEOUT_ERROR,
            message=error_message,
            retryable=True,
            retry_delay_multiplier=1.5,
            max_retries=3,
        )

    # Validation errors
    if (
        isinstance(error, (ValueError, TypeError))
        or "validation" in error_message.lower()
    ):
        return TaskError(
            type=TaskErrorType.VALIDATION_ERROR,
            message=error_message,
            retryable=False,
            max_retries=0,
        )

    # Permission errors
    if "permission" in error_message.lower() or "unauthorized" in error_message.lower():
        return TaskError(
            type=TaskErrorType.PERMISSION_ERROR,
            message=error_message,
            retryable=False,
            max_retries=0,
        )

    # Resource errors (memory, disk, etc.)
    if any(
        keyword in error_message.lower()
        for keyword in ["memory", "disk", "resource", "quota"]
    ):
        return TaskError(
            type=TaskErrorType.RESOURCE_ERROR,
            message=error_message,
            retryable=True,
            retry_delay_multiplier=3.0,  # Longer delay for resource issues
            max_retries=2,
        )

    # External service errors
    if any(
        keyword in error_message.lower()
        for keyword in ["api", "service", "external", "third-party"]
    ):
        return TaskError(
            type=TaskErrorType.EXTERNAL_SERVICE_ERROR,
            message=error_message,
            retryable=True,
            retry_delay_multiplier=2.0,
            max_retries=4,
        )

    # Programming errors
    if isinstance(error, (AttributeError, KeyError, IndexError, ImportError)):
        return TaskError(
            type=TaskErrorType.PROGRAMMING_ERROR,
            message=error_message,
            retryable=False,
            max_retries=0,
        )

    # Unknown errors
    return TaskError(
        type=TaskErrorType.UNKNOWN_ERROR,
        message=error_message,
        retryable=True,
        retry_delay_multiplier=1.0,
        max_retries=3,
    )


@dataclass
class Task:
    id: str
    name: str
    func_name: str
    args: tuple
    kwargs: dict
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    error_type: Optional[TaskErrorType] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 300
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    processing_time: Optional[float] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        data = asdict(self)
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        data["error_type"] = self.error_type.value if self.error_type else None
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        data["priority"] = TaskPriority(data["priority"])
        data["status"] = TaskStatus(data["status"])
        if data.get("error_type"):
            data["error_type"] = TaskErrorType(data["error_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class ScheduledJob:
    id: str
    name: str
    func_name: str
    cron_expression: str
    args: tuple
    kwargs: dict
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.next_run is None:
            self._calculate_next_run()

    def _calculate_next_run(self):
        """Calculate next run time based on cron expression"""
        try:
            cron = croniter(self.cron_expression, datetime.utcnow())
            self.next_run = cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression {self.cron_expression}: {e}")
            self.next_run = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.last_run:
            data["last_run"] = self.last_run.isoformat()
        if self.next_run:
            data["next_run"] = self.next_run.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledJob":
        """Create job from dictionary"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("last_run"):
            data["last_run"] = datetime.fromisoformat(data["last_run"])
        if data.get("next_run"):
            data["next_run"] = datetime.fromisoformat(data["next_run"])
        return cls(**data)


class BackgroundWorker:
    """Background worker for processing async tasks"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_workers: int = 10,
        task_timeout: int = 300,
        max_retries: int = 3,
        retry_delay: int = 60,
    ):
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Redis connection
        self.redis = None

        # Task registry
        self.task_registry: Dict[str, Callable] = {}

        # Worker state
        self.workers: List[asyncio.Task] = []
        self.running = False

        # Enhanced metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "tasks_cancelled": 0,
            "total_processing_time": 0,
            "avg_processing_time": 0,
            "error_counts": {error_type.value: 0 for error_type in TaskErrorType},
            "task_type_counts": {},
            "worker_health": {},
            "queue_size": 0,
            "last_activity": None,
        }

    async def start(self):
        """Start the background worker"""
        try:
            # Connect to Redis
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()

            # Start workers
            self.running = True
            self._start_time = time.time()  # Track uptime

            for i in range(self.max_workers):
                worker = asyncio.create_task(self._worker(f"worker-{i}"))
                self.workers.append(worker)

            logger.info(f"Background worker started with {self.max_workers} workers")

        except Exception as e:
            logger.error(f"Failed to start background worker: {e}")
            raise

    async def stop(self):
        """Stop the background worker"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Close Redis connection
        if self.redis:
            await self.redis.close()

        logger.info("Background worker stopped")

    def register_task(self, name: str, func: Callable):
        """Register a task function"""
        self.task_registry[name] = func
        logger.info(f"Registered task: {name}")

    async def enqueue_task(
        self,
        name: str,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: int = None,
        max_retries: int = None,
        retry_delay: int = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """Enqueue a task for processing"""
        if name not in self.task_registry:
            raise ValueError(f"Task '{name}' not registered")

        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            func_name=name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            timeout=timeout or self.task_timeout,
            max_retries=max_retries or self.max_retries,
            retry_delay=retry_delay or self.retry_delay,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Store task in Redis
        await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

        # Add to priority queue
        score = time.time() + (priority.value * 1000)  # Higher priority = higher score
        await self.redis.zadd("task_queue", {task_id: score})

        logger.info(f"Enqueued task {task_id} ({name}) with priority {priority.name}")
        return task_id

    async def _worker(self, worker_id: str):
        """Worker coroutine for processing tasks"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get next task from queue
                task_data = await self.redis.zpopmin("task_queue", count=1)

                if not task_data:
                    await asyncio.sleep(1)
                    continue

                task_id = task_data[0][0]
                await self._process_task(worker_id, task_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def _process_task(self, worker_id: str, task_id: str):
        """Process a single task with enhanced error handling and monitoring"""
        start_time = time.time()
        task = None

        try:
            # Get task data
            task_data = await self.redis.hgetall(f"task:{task_id}")
            if not task_data:
                logger.warning(f"Task {task_id} not found")
                return

            task = Task.from_dict(task_data)

            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

            logger.info(f"Worker {worker_id} processing task {task_id} ({task.name})")

            # Get task function
            func = self.task_registry.get(task.func_name)
            if not func:
                raise ValueError(f"Task function '{task.func_name}' not found")

            # Execute task with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*task.args, **task.kwargs), timeout=task.timeout
                )
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *task.args, **task.kwargs),
                    timeout=task.timeout,
                )

            processing_time = time.time() - start_time

            # Update task with success
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.processing_time = processing_time
            await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

            # Update metrics
            await self._update_metrics(task, processing_time, success=True)

            logger.info(
                f"Task {task_id} completed successfully in {processing_time:.2f}s"
            )

        except asyncio.TimeoutError as e:
            processing_time = time.time() - start_time
            await self._handle_task_failure(
                task_id,
                f"Task timeout after {processing_time:.2f}s",
                worker_id,
                e,
                processing_time,
            )
        except Exception as e:
            processing_time = time.time() - start_time
            await self._handle_task_failure(
                task_id, str(e), worker_id, e, processing_time
            )

    async def _handle_task_failure(
        self,
        task_id: str,
        error_message: str,
        worker_id: str,
        original_error: Exception,
        processing_time: float,
    ):
        """Handle task failure with enhanced retry logic and error categorization"""
        try:
            task_data = await self.redis.hgetall(f"task:{task_id}")
            if not task_data:
                return

            task = Task.from_dict(task_data)

            # Categorize the error
            task_error = categorize_task_error(original_error)
            task.error = error_message
            task.error_type = task_error.type
            task.processing_time = processing_time

            # Log error with context
            logger.error(
                f"Task {task_id} failed: {error_message}",
                extra={
                    "task_id": task_id,
                    "task_name": task.name,
                    "worker_id": worker_id,
                    "error_type": task_error.type.value,
                    "retryable": task_error.retryable,
                    "processing_time": processing_time,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "traceback": traceback.format_exc(),
                },
            )

            # Check if we should retry based on error categorization
            should_retry = task_error.retryable and task.retry_count < min(
                task_error.max_retries, task.max_retries
            )

            if should_retry:
                # Calculate retry delay with exponential backoff
                base_delay = task.retry_delay
                delay_multiplier = task_error.retry_delay_multiplier
                retry_delay = int(base_delay * (delay_multiplier**task.retry_count))

                task.retry_count += 1
                task.status = TaskStatus.RETRY
                await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

                # Re-queue with calculated delay
                score = time.time() + retry_delay + (task.priority.value * 1000)
                await self.redis.zadd("task_queue", {task_id: score})

                self.metrics["tasks_retried"] += 1
                logger.warning(
                    f"Task {task_id} failed ({task_error.type.value}), "
                    f"retrying in {retry_delay}s ({task.retry_count}/{min(task_error.max_retries, task.max_retries)})"
                )
            else:
                # Mark as failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

                # Update metrics for failed task
                await self._update_metrics(task, processing_time, success=False)

                logger.error(
                    f"Task {task_id} failed permanently after {task.retry_count} retries: {error_message}"
                )

        except Exception as e:
            logger.error(f"Error handling task failure for {task_id}: {e}")
            # Mark task as failed if we can't handle the failure
            try:
                task_data = await self.redis.hgetall(f"task:{task_id}")
                if task_data:
                    task = Task.from_dict(task_data)
                    task.status = TaskStatus.FAILED
                    task.error = f"Error handling failure: {str(e)}"
                    task.completed_at = datetime.utcnow()
                    await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())
            except Exception:
                pass

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get task status by ID"""
        try:
            task_data = await self.redis.hgetall(f"task:{task_id}")
            if task_data:
                return Task.from_dict(task_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        try:
            task_data = await self.redis.hgetall(f"task:{task_id}")
            if not task_data:
                return False

            task = Task.from_dict(task_data)
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                await self.redis.hset(f"task:{task_id}", mapping=task.to_dict())

                # Remove from queue
                await self.redis.zrem("task_queue", task_id)

                # Update metrics
                self.metrics["tasks_cancelled"] += 1

                logger.info(f"Task {task_id} cancelled")
                return True

            return False

        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return False

    async def _update_metrics(
        self, task: Task, processing_time: float, success: bool = True
    ):
        """Update metrics with task execution results"""
        self.metrics["total_processing_time"] += processing_time

        if success:
            self.metrics["tasks_processed"] += 1
        else:
            self.metrics["tasks_failed"] += 1
            if task.error_type:
                self.metrics["error_counts"][task.error_type.value] += 1

        # Update task type counts
        task_type = task.name
        self.metrics["task_type_counts"][task_type] = (
            self.metrics["task_type_counts"].get(task_type, 0) + 1
        )

        # Update average processing time
        total_tasks = self.metrics["tasks_processed"] + self.metrics["tasks_failed"]
        if total_tasks > 0:
            self.metrics["avg_processing_time"] = (
                self.metrics["total_processing_time"] / total_tasks
            )

        self.metrics["last_activity"] = datetime.utcnow().isoformat()

    async def _update_queue_metrics(self):
        """Update queue-related metrics"""
        try:
            if self.redis:
                queue_size = await self.redis.zcard("task_queue")
                self.metrics["queue_size"] = queue_size
        except Exception as e:
            logger.warning(f"Failed to update queue metrics: {e}")

    async def _update_worker_health(self):
        """Update worker health metrics"""
        try:
            for i, worker in enumerate(self.workers):
                worker_id = f"worker-{i}"
                self.metrics["worker_health"][worker_id] = {
                    "status": "running" if not worker.done() else "stopped",
                    "exception": (
                        str(worker.exception())
                        if worker.done() and worker.exception()
                        else None
                    ),
                    "last_activity": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.warning(f"Failed to update worker health: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive worker metrics"""
        # Update real-time metrics
        asyncio.create_task(self._update_queue_metrics())
        asyncio.create_task(self._update_worker_health())

        # Calculate additional metrics
        total_tasks = self.metrics["tasks_processed"] + self.metrics["tasks_failed"]
        success_rate = 0
        if total_tasks > 0:
            success_rate = (self.metrics["tasks_processed"] / total_tasks) * 100

        # Get error distribution
        error_distribution = {}
        total_errors = sum(self.metrics["error_counts"].values())
        if total_errors > 0:
            for error_type, count in self.metrics["error_counts"].items():
                if count > 0:
                    error_distribution[error_type] = {
                        "count": count,
                        "percentage": (count / total_errors) * 100,
                    }

        return {
            **self.metrics,
            "success_rate": success_rate,
            "error_distribution": error_distribution,
            "active_workers": len([w for w in self.workers if not w.done()]),
            "running": self.running,
            "uptime": self._get_uptime(),
            "health_status": self._get_health_status(),
        }

    def _get_uptime(self) -> Optional[float]:
        """Get worker uptime in seconds"""
        if hasattr(self, "_start_time"):
            return time.time() - self._start_time
        return None

    def _get_health_status(self) -> str:
        """Get overall health status"""
        if not self.running:
            return "stopped"

        active_workers = len([w for w in self.workers if not w.done()])
        if active_workers == 0:
            return "unhealthy"
        elif active_workers < self.max_workers:
            return "degraded"
        else:
            return "healthy"

    async def get_health_check(self) -> Dict[str, Any]:
        """Get detailed health check information"""
        try:
            # Check Redis connection
            redis_healthy = False
            if self.redis:
                try:
                    await self.redis.ping()
                    redis_healthy = True
                except Exception:
                    pass

            # Check worker status
            active_workers = len([w for w in self.workers if not w.done()])
            worker_healthy = active_workers > 0

            # Check queue health
            queue_healthy = True
            if self.redis:
                try:
                    queue_size = await self.redis.zcard("task_queue")
                    # Consider queue unhealthy if it's too large
                    queue_healthy = queue_size < 1000
                except Exception:
                    queue_healthy = False

            overall_health = redis_healthy and worker_healthy and queue_healthy

            return {
                "status": "healthy" if overall_health else "unhealthy",
                "checks": {
                    "redis": {
                        "status": "healthy" if redis_healthy else "unhealthy",
                        "details": (
                            "Redis connection is working"
                            if redis_healthy
                            else "Redis connection failed"
                        ),
                    },
                    "workers": {
                        "status": "healthy" if worker_healthy else "unhealthy",
                        "details": f"{active_workers}/{self.max_workers} workers active",
                    },
                    "queue": {
                        "status": "healthy" if queue_healthy else "unhealthy",
                        "details": (
                            "Queue size is normal"
                            if queue_healthy
                            else "Queue size is too large"
                        ),
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


class JobScheduler:
    """Job scheduler for recurring tasks"""

    def __init__(self, worker: BackgroundWorker):
        self.worker = worker
        self.redis = worker.redis
        self.jobs: Dict[str, ScheduledJob] = {}
        self.scheduler_task = None
        self.running = False

    async def start(self):
        """Start the job scheduler"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Job scheduler started")

    async def stop(self):
        """Stop the job scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Job scheduler stopped")

    async def add_job(
        self,
        name: str,
        func_name: str,
        cron_expression: str,
        *args,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> str:
        """Add a scheduled job"""
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            id=job_id,
            name=name,
            func_name=func_name,
            cron_expression=cron_expression,
            args=args,
            kwargs=kwargs,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Store job in Redis
        await self.redis.hset(f"job:{job_id}", mapping=job.to_dict())
        self.jobs[job_id] = job

        logger.info(
            f"Added scheduled job {job_id} ({name}) with cron: {cron_expression}"
        )
        return job_id

    async def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            await self.redis.delete(f"job:{job_id}")
            logger.info(f"Removed scheduled job {job_id}")
            return True
        return False

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.utcnow()

                # Check all jobs
                for job_id, job in self.jobs.items():
                    if not job.enabled:
                        continue

                    if job.next_run and now >= job.next_run:
                        # Execute job
                        await self._execute_job(job)

                        # Update next run time
                        job.last_run = now
                        job._calculate_next_run()
                        await self.redis.hset(f"job:{job_id}", mapping=job.to_dict())

                # Sleep for 1 minute
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job"""
        try:
            logger.info(f"Executing scheduled job {job.id} ({job.name})")

            # Enqueue task
            await self.worker.enqueue_task(
                job.func_name,
                *job.args,
                tags=job.tags,
                metadata=job.metadata,
                **job.kwargs,
            )

        except Exception as e:
            logger.error(f"Error executing scheduled job {job.id}: {e}")


# Global worker and scheduler instances
background_worker = BackgroundWorker()
job_scheduler = JobScheduler(background_worker)


# Task decorators
def background_task(
    name: str = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: int = 300,
    max_retries: int = 3,
    retry_delay: int = 60,
):
    """Decorator to register a background task"""

    def decorator(func):
        task_name = name or func.__name__
        background_worker.register_task(task_name, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return background_worker.enqueue_task(
                task_name,
                *args,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay,
                **kwargs,
            )

        return wrapper

    return decorator


def scheduled_job(cron_expression: str, name: str = None):
    """Decorator to register a scheduled job"""

    def decorator(func):
        job_name = name or func.__name__
        background_worker.register_task(job_name, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return job_scheduler.add_job(
                job_name,
                job_name,
                cron_expression,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator
