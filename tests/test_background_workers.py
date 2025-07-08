from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from middleware.error_handler import RateLimitError
from services.background_workers import (
    BackgroundWorker,
    JobScheduler,
    ScheduledJob,
    Task,
    TaskErrorType,
    TaskPriority,
    TaskStatus,
    background_task,
    categorize_task_error,
    scheduled_job,
)


class TestBackgroundWorkerModels:
    def test_task_to_dict_and_from_dict(self) -> None:
        now = datetime.utcnow()
        task = Task(
            id="1",
            name="test",
            func_name="f",
            args=(1,),
            kwargs={},
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            created_at=now,
        )
        d = task.to_dict()
        t2 = Task.from_dict(d)
        assert t2.id == "1"
        assert t2.priority == TaskPriority.HIGH
        assert t2.status == TaskStatus.PENDING
        assert t2.created_at == now

    def test_scheduled_job_to_dict_and_from_dict(self) -> None:
        now = datetime.utcnow()
        job = ScheduledJob(
            id="j1",
            name="job",
            func_name="f",
            cron_expression="* * * * *",
            args=(),
            kwargs={},
            created_at=now,
        )
        d = job.to_dict()
        j2 = ScheduledJob.from_dict(d)
        assert j2.id == "j1"
        assert j2.cron_expression == "* * * * *"
        assert j2.created_at == now


class TestTaskErrorCategorization:
    def test_timeout_error(self) -> None:
        e = TimeoutError("timeout!")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.TIMEOUT_ERROR
        assert err.retryable

    def test_rate_limit_error(self) -> None:
        e = RateLimitError("rate limit!")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.EXTERNAL_SERVICE_ERROR

    def test_network_error(self) -> None:
        e = ConnectionError("conn fail")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.NETWORK_ERROR

    def test_validation_error(self) -> None:
        e = ValueError("validation failed")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.VALIDATION_ERROR
        assert not err.retryable

    def test_permission_error(self) -> None:
        e = Exception("permission denied")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.PERMISSION_ERROR

    def test_resource_error(self) -> None:
        e = Exception("memory error")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.RESOURCE_ERROR

    def test_external_service_error(self) -> None:
        e = Exception("api error")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.EXTERNAL_SERVICE_ERROR

    def test_programming_error(self) -> None:
        e = KeyError("bad key")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.PROGRAMMING_ERROR
        assert not err.retryable

    def test_unknown_error(self) -> None:
        e = Exception("something else")
        err = categorize_task_error(e)
        assert err.type == TaskErrorType.UNKNOWN_ERROR


class TestBackgroundWorkerCore:
    @pytest.fixture
    def worker(self) -> None:
        return BackgroundWorker(redis_url="redis://localhost:6379", max_workers=2)

    @pytest.mark.asyncio
    async def test_register_and_enqueue_task(self, worker):
        pass
        async def dummy(*args, **kwargs):
            pass
            return "ok"

        worker.register_task("dummy", dummy)
        with patch.object(worker, "redis", new=AsyncMock()):
            task_id = await worker.enqueue_task(
                "dummy", 1, 2, priority=TaskPriority.NORMAL
            )
            assert isinstance(task_id, str)

    @pytest.mark.asyncio
    async def test_start_and_stop(self, worker):
        pass
        with patch.object(worker, "redis", new=AsyncMock()):
            await worker.start()
            await worker.stop()

    @pytest.mark.asyncio
    async def test_get_task_status_and_cancel(self, worker):
        pass
        with patch.object(worker, "redis", new=AsyncMock()):
            # Simulate no task found
            status = await worker.get_task_status("notask")
            assert status is None
            cancelled = await worker.cancel_task("notask")
            assert not cancelled

    @pytest.mark.asyncio
    async def test_worker_process_and_failure(self, worker):
        pass
        async def fail(*a, **k):
            pass
            raise ValueError("fail")

        worker.register_task("fail", fail)
        with patch.object(worker, "redis", new=AsyncMock()):
            # Simulate _process_task error handling
            await worker._handle_task_failure(
                task_id="tid",
                error_message="fail",
                worker_id="wid",
                original_error=ValueError("fail"),
                processing_time=0.1,
            )

    def test_metrics_and_health(self, worker) -> None:
        with patch("asyncio.create_task") as mock_create_task:
            m = worker.get_metrics()
            assert "uptime" in m
            assert "active_workers" in m  # This key actually exists
            assert worker._get_health_status() in (
                "healthy",
                "degraded",
                "unhealthy",
                "stopped",
            )


class TestJobScheduler:
    @pytest.mark.asyncio
    async def test_add_and_remove_job(self):
        pass
        worker = BackgroundWorker()
        scheduler = JobScheduler(worker)
        with patch.object(scheduler, "jobs", new={}):
            with patch.object(scheduler, "redis", new=AsyncMock()):
                job_id = await scheduler.add_job("job", "func", "* * * * *")
                assert isinstance(job_id, str)
                removed = await scheduler.remove_job(job_id)
                assert removed

    @pytest.mark.asyncio
    async def test_scheduler_loop_and_execute_job(self):
        pass
        worker = BackgroundWorker()
        scheduler = JobScheduler(worker)
        job = ScheduledJob(
            id="jid",
            name="job",
            func_name="func",
            cron_expression="* * * * *",
            args=(),
            kwargs={},
        )
        with patch.object(scheduler, "jobs", new={job.id: job}):
            with patch.object(scheduler, "_execute_job", new=AsyncMock()):
                # Run one iteration of the scheduler loop
                async def stop_after_one():
                    pass
                    await asyncio.sleep(0.01)
                    scheduler.running = False

                asyncio.create_task(stop_after_one())
                await scheduler._scheduler_loop()

    @pytest.mark.asyncio
    async def test_execute_job(self):
        pass
        worker = BackgroundWorker()
        scheduler = JobScheduler(worker)
        job = ScheduledJob(
            id="jid",
            name="job",
            func_name="func",
            cron_expression="* * * * *",
            args=(),
            kwargs={},
        )
        with patch.object(worker, "enqueue_task", new=AsyncMock(return_value="tid")):
            await scheduler._execute_job(job)


class TestDecorators:
    @patch("services.background_workers.background_worker")
    def test_background_task_decorator(self, mock_worker) -> None:
        # Mock the global background_worker instance
        mock_worker.enqueue_task = AsyncMock(return_value="task_id_123")

        @background_task(name="test", priority=TaskPriority.HIGH)
        def f(x) -> None:
            return x + 1

        assert callable(f)
        # The decorator returns a coroutine, so we need to await it
        import asyncio

        result = asyncio.run(f(5))
        assert result == "task_id_123"  # The task ID, not the function result

    @patch("services.background_workers.job_scheduler")
    def test_scheduled_job_decorator(self, mock_scheduler) -> None:
        # Mock the global job_scheduler instance
        mock_scheduler.add_job = AsyncMock(return_value="job_id_456")

        @scheduled_job(cron_expression="* * * * *", name="sched")
        def f(x) -> None:
            return x * 2

        assert callable(f)
        # The decorator returns a coroutine, so we need to await it
        import asyncio

        result = asyncio.run(f(5))
        assert result == "job_id_456"  # The job ID, not the function result
