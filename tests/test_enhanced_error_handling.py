"""
Comprehensive tests for enhanced error handling and monitoring systems.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from middleware.error_handler import (
    APIError,
    AuthenticationError,
    ErrorTracker,
    RateLimitError,
    ValidationError,
    categorize_error,
)
from services.background_tasks import (
    BackgroundTaskManager,
    TaskMetrics,
    log_background_task,
)
from services.background_workers import (
    BackgroundWorker,
    Task,
    TaskErrorType,
    TaskPriority,
    TaskStatus,
    categorize_task_error,
)
from services.notion.sync_manager import (
    ConflictResolution,
    NotionSyncManager,
    SyncDirection,
    SyncStatus,
)


class TestErrorCategorization:
    """Test error categorization functionality."""

    def test_network_error_categorization(self):
        """Test network error categorization."""
        error = ConnectionError("Connection failed")
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.NETWORK_ERROR
        assert task_error.retryable is True
        assert task_error.retry_delay_multiplier == 2.0
        assert task_error.max_retries == 5

    def test_timeout_error_categorization(self):
        """Test timeout error categorization."""
        error = TimeoutError()
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.TIMEOUT_ERROR
        assert task_error.retryable is True
        assert task_error.retry_delay_multiplier == 1.5
        assert task_error.max_retries == 3

    def test_validation_error_categorization(self):
        """Test validation error categorization."""
        error = ValueError("Invalid input")
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.VALIDATION_ERROR
        assert task_error.retryable is False
        assert task_error.max_retries == 0

    def test_permission_error_categorization(self):
        """Test permission error categorization."""
        error = Exception("Permission denied")
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.PERMISSION_ERROR
        assert task_error.retryable is False
        assert task_error.max_retries == 0

    def test_resource_error_categorization(self):
        """Test resource error categorization."""
        error = Exception("Memory limit exceeded")
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.RESOURCE_ERROR
        assert task_error.retryable is True
        assert task_error.retry_delay_multiplier == 3.0
        assert task_error.max_retries == 2

    def test_external_service_error_categorization(self):
        """Test external service error categorization."""
        error = Exception("API service unavailable")
        task_error = categorize_task_error(error)

        assert task_error.type == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert task_error.retryable is True
        assert task_error.retry_delay_multiplier == 2.0
        assert task_error.max_retries == 4


class TestBackgroundWorkers:
    """Test enhanced background worker functionality."""

    @pytest.fixture
    async def worker(self):
        """Create a test worker instance."""
        worker = BackgroundWorker(
            redis_url="redis://localhost:6379",
            max_workers=2,
            task_timeout=30,
            max_retries=3,
            retry_delay=5,
        )

        # Mock Redis connection
        worker.redis = AsyncMock()
        worker.redis.ping.return_value = True
        worker.redis.hset.return_value = True
        worker.redis.hgetall.return_value = {}
        worker.redis.zadd.return_value = True
        worker.redis.zpopmin.return_value = []
        worker.redis.zrem.return_value = True
        worker.redis.zcard.return_value = 0

        return worker

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="test-task-1",
            name="test_task",
            func_name="test_task",
            args=(),
            kwargs={},
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            created_at=datetime.now(UTC),
            max_retries=3,
            retry_delay=5,
        )

    async def test_worker_initialization(self, worker):
        """Test worker initialization."""
        assert worker.max_workers == 2
        assert worker.task_timeout == 30
        assert worker.max_retries == 3
        assert worker.retry_delay == 5
        assert len(worker.metrics["error_counts"]) == len(TaskErrorType)

    async def test_task_enqueue(self, worker, sample_task):
        """Test task enqueueing."""

        # Register a test task
        async def test_task_func():
            return "success"

        worker.register_task("test_task", test_task_func)

        # Mock Redis operations
        worker.redis.hset.return_value = True
        worker.redis.zadd.return_value = True

        task_id = await worker.enqueue_task("test_task", priority=TaskPriority.HIGH)

        assert task_id is not None
        assert worker.redis.hset.called
        assert worker.redis.zadd.called

    async def test_task_processing_success(self, worker, sample_task):
        """Test successful task processing."""

        # Register a test task
        async def test_task_func():
            return "success"

        worker.register_task("test_task", test_task_func)

        # Mock task data
        task_data = sample_task.to_dict()
        worker.redis.hgetall.return_value = task_data

        # Process task
        await worker._process_task("worker-1", sample_task.id)

        # Check metrics
        assert worker.metrics["tasks_processed"] == 1
        assert worker.metrics["tasks_failed"] == 0

    async def test_task_processing_failure(self, worker, sample_task):
        """Test task processing failure with retry logic."""

        # Register a failing task
        async def failing_task_func():
            raise ConnectionError("Network error")

        worker.register_task("test_task", failing_task_func)

        # Mock task data
        task_data = sample_task.to_dict()
        worker.redis.hgetall.return_value = task_data

        # Process task
        await worker._process_task("worker-1", sample_task.id)

        # Check metrics
        assert worker.metrics["tasks_failed"] == 1
        assert worker.metrics["error_counts"]["network_error"] == 1

    async def test_worker_health_check(self, worker):
        """Test worker health check."""
        # Mock workers
        worker.workers = [Mock(), Mock()]
        worker.workers[0].done.return_value = False
        worker.workers[1].done.return_value = False
        worker.running = True

        health = await worker.get_health_check()

        assert health["status"] == "healthy"
        assert "redis" in health["checks"]
        assert "workers" in health["checks"]
        assert "queue" in health["checks"]

    async def test_worker_metrics(self, worker):
        """Test worker metrics collection."""
        # Add some test data
        worker.metrics["tasks_processed"] = 10
        worker.metrics["tasks_failed"] = 2
        worker.metrics["total_processing_time"] = 100.0

        metrics = worker.get_metrics()

        assert metrics["success_rate"] == 83.33  # 10/(10+2) * 100
        assert metrics["avg_processing_time"] == 8.33  # 100/12
        assert metrics["health_status"] == "healthy"


class TestBackgroundTaskManager:
    """Test enhanced background task manager."""

    @pytest.fixture
    def task_manager(self):
        """Create a test task manager."""
        background_tasks = Mock()
        return BackgroundTaskManager(background_tasks)

    def test_task_metrics_initialization(self):
        """Test task metrics initialization."""
        metrics = TaskMetrics()

        assert metrics.tasks_started == 0
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert len(metrics.error_counts) == 8  # Number of error types

    def test_task_metrics_recording(self):
        """Test task metrics recording."""
        metrics = TaskMetrics()

        # Record task start
        metrics.record_task_start("test_task")
        assert metrics.tasks_started == 1
        assert metrics.task_type_counts["test_task"] == 1

        # Record task completion
        metrics.record_task_completion(5.0)
        assert metrics.tasks_completed == 1
        assert metrics.total_processing_time == 5.0

        # Record task failure
        metrics.record_task_failure(TaskErrorType.NETWORK_ERROR, 3.0)
        assert metrics.tasks_failed == 1
        assert metrics.error_counts["network_error"] == 1
        assert metrics.total_processing_time == 8.0

    def test_task_metrics_summary(self):
        """Test task metrics summary calculation."""
        metrics = TaskMetrics()

        # Add some test data
        metrics.record_task_start("task1")
        metrics.record_task_start("task2")
        metrics.record_task_completion(10.0)
        metrics.record_task_failure(TaskErrorType.NETWORK_ERROR, 5.0)

        summary = metrics.get_summary()

        assert summary["tasks_started"] == 2
        assert summary["tasks_completed"] == 1
        assert summary["tasks_failed"] == 1
        assert summary["success_rate"] == 50.0
        assert summary["avg_processing_time"] == 7.5

    async def test_background_task_decorator(self):
        """Test background task decorator."""

        @log_background_task
        async def test_task():
            return "success"

        result = await test_task()
        assert result == "success"

        # Check metrics were recorded
        from services.background_tasks import task_metrics

        assert task_metrics.tasks_started == 1
        assert task_metrics.tasks_completed == 1

    async def test_background_task_decorator_with_error(self):
        """Test background task decorator with error handling."""

        @log_background_task
        async def failing_task():
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            await failing_task()

        # Check metrics were recorded
        from services.background_tasks import task_metrics

        assert task_metrics.tasks_started == 2  # Previous test + this one
        assert task_metrics.tasks_failed == 1
        assert task_metrics.error_counts["network_error"] == 1

    def test_task_manager_health_status(self, task_manager):
        """Test task manager health status."""
        # Mock metrics
        with patch("services.background_tasks.task_metrics") as mock_metrics:
            mock_metrics.get_summary.return_value = {
                "tasks_completed": 90,
                "tasks_failed": 10,
                "success_rate": 90.0,
            }

            health = task_manager.get_health_status()

            assert health["status"] == "healthy"
            assert health["success_rate"] == 90.0
            assert health["error_rate"] == 10.0


class TestNotionSyncManager:
    """Test enhanced Notion sync manager."""

    @pytest.fixture
    def sync_manager(self):
        """Create a test sync manager."""
        notion_client = Mock()
        flashcard_generator = Mock()
        return NotionSyncManager(notion_client, flashcard_generator)

    def test_sync_direction_enum(self):
        """Test sync direction enumeration."""
        assert SyncDirection.NOTION_TO_COGNIE.value == "notion_to_cognie"
        assert SyncDirection.COGNIE_TO_NOTION.value == "cognie_to_notion"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"

    def test_conflict_resolution_model(self):
        """Test conflict resolution model."""
        resolution = ConflictResolution(
            strategy="notion_wins",
            resolved_at=datetime.now(UTC),
            resolved_by="system",
            details={"test": "data"},
        )

        assert resolution.strategy == "notion_wins"
        assert resolution.resolved_by == "system"
        assert resolution.details["test"] == "data"

    def test_recoverable_error_detection(self, sync_manager):
        """Test recoverable error detection."""
        # Test recoverable errors
        assert sync_manager._is_recoverable_error(Exception("Connection timeout"))
        assert sync_manager._is_recoverable_error(Exception("Rate limit exceeded"))
        assert sync_manager._is_recoverable_error(
            Exception("Service temporarily unavailable")
        )

        # Test non-recoverable errors
        assert not sync_manager._is_recoverable_error(Exception("Invalid input"))
        assert not sync_manager._is_recoverable_error(Exception("Permission denied"))

    async def test_content_merging(self, sync_manager):
        """Test content merging functionality."""
        local_content = "Line 1\nLine 2\nLine 3"
        notion_content = "Line 2\nLine 3\nLine 4"

        merged = await sync_manager._merge_content(local_content, notion_content)

        # Should contain all unique lines
        assert "Line 1" in merged
        assert "Line 2" in merged
        assert "Line 3" in merged
        assert "Line 4" in merged

    async def test_sync_health_status(self, sync_manager):
        """Test sync health status calculation."""
        # Mock user sync history
        with patch.object(sync_manager, "get_user_sync_history") as mock_history:
            mock_history.return_value = [
                SyncStatus(
                    user_id="user1",
                    notion_page_id="page1",
                    last_sync_time=datetime.now(UTC),
                    sync_direction="notion_to_cognie",
                    status="success",
                    items_synced=5,
                ),
                SyncStatus(
                    user_id="user1",
                    notion_page_id="page2",
                    last_sync_time=datetime.now(UTC),
                    sync_direction="notion_to_cognie",
                    status="failed",
                    items_synced=0,
                ),
            ]

            with patch.object(
                sync_manager, "_get_pending_retries_count"
            ) as mock_retries:
                mock_retries.return_value = 0

                health = await sync_manager.get_sync_health_status("user1")

                assert health["status"] == "degraded"  # 50% success rate
                assert health["success_rate"] == 50.0
                assert health["total_syncs"] == 2
                assert health["successful_syncs"] == 1


class TestErrorHandler:
    """Test enhanced error handler middleware."""

    def test_api_error_classes(self):
        """Test API error classes."""
        # Test ValidationError
        val_error = ValidationError("Invalid input", {"field": "value"})
        assert val_error.status_code == 422
        assert val_error.error_code == "VALIDATION_ERROR"
        assert val_error.details["field"] == "value"

        # Test AuthenticationError
        auth_error = AuthenticationError("Invalid credentials")
        assert auth_error.status_code == 401
        assert auth_error.error_code == "AUTHENTICATION_ERROR"

        # Test RateLimitError
        rate_error = RateLimitError("Too many requests", 60)
        assert rate_error.status_code == 429
        assert rate_error.error_code == "RATE_LIMIT_EXCEEDED"
        assert rate_error.retry_after == 60

    def test_error_categorization(self):
        """Test error categorization."""
        # Test API error
        api_error = APIError("Test error", 500)
        error_info = categorize_error(api_error)
        assert error_info["category"] == "api_error"
        assert error_info["severity"] == "high"
        assert error_info["retryable"] is True

        # Test validation error
        val_error = ValidationError("Invalid input")
        error_info = categorize_error(val_error)
        assert error_info["category"] == "validation_error"
        assert error_info["severity"] == "low"
        assert error_info["retryable"] is False

    def test_error_tracker(self):
        """Test error tracker functionality."""
        tracker = ErrorTracker()

        # Track some errors
        tracker.track_error({"category": "network_error", "severity": "medium"})
        tracker.track_error({"category": "network_error", "severity": "medium"})
        tracker.track_error({"category": "validation_error", "severity": "low"})

        # Check counts
        assert tracker.error_counts["network_error:medium"] == 2
        assert tracker.error_counts["validation_error:low"] == 1


class TestRateLimitingScenarios:
    """Test rate limiting scenarios."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test rate limit error handling."""
        # Simulate rate limit error
        error = RateLimitError("Rate limit exceeded", 60)

        # Test error categorization
        error_info = categorize_error(error)
        assert error_info["category"] == "api_error"
        assert error_info["retryable"] is True

        # Test retry logic
        task_error = categorize_task_error(error)
        assert task_error.type == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert task_error.retryable is True
        assert task_error.max_retries == 4


class TestNetworkFailureRecovery:
    """Test network failure recovery."""

    @pytest.mark.asyncio
    async def test_network_error_recovery(self):
        """Test network error recovery strategies."""
        # Test different network errors
        network_errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timeout"),
            TimeoutError(),
        ]

        for error in network_errors:
            task_error = categorize_task_error(error)
            assert task_error.type == TaskErrorType.NETWORK_ERROR
            assert task_error.retryable is True
            assert task_error.retry_delay_multiplier == 2.0
            assert task_error.max_retries == 5

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        base_delay = 60
        delay_multiplier = 2.0

        # Calculate delays for different retry attempts
        delays = []
        for attempt in range(3):
            delay = int(base_delay * (delay_multiplier**attempt))
            delays.append(delay)

        # Should be exponential: 60, 120, 240
        assert delays[0] == 60
        assert delays[1] == 120
        assert delays[2] == 240


if __name__ == "__main__":
    pytest.main([__file__])
