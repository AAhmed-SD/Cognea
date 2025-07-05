import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from services.background_tasks import (
    BackgroundTaskManager,
    TaskErrorType,
    TaskMetrics,
    TaskStatus,
    categorize_task_error,
    log_background_task,
    task_metrics,
)


class TestTaskErrorType:
    """Test TaskErrorType enum"""

    def test_task_error_type_values(self):
        """Test that all TaskErrorType values are correct"""
        assert TaskErrorType.NETWORK_ERROR.value == "network_error"
        assert TaskErrorType.TIMEOUT_ERROR.value == "timeout_error"
        assert TaskErrorType.VALIDATION_ERROR.value == "validation_error"
        assert TaskErrorType.PERMISSION_ERROR.value == "permission_error"
        assert TaskErrorType.RESOURCE_ERROR.value == "resource_error"
        assert TaskErrorType.EXTERNAL_SERVICE_ERROR.value == "external_service_error"
        assert TaskErrorType.PROGRAMMING_ERROR.value == "programming_error"
        assert TaskErrorType.UNKNOWN_ERROR.value == "unknown_error"


class TestTaskStatus:
    """Test TaskStatus enum"""

    def test_task_status_values(self):
        """Test that all TaskStatus values are correct"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRY.value == "retry"


class TestCategorizeTaskError:
    """Test the categorize_task_error function"""

    def test_network_error_categorization(self):
        """Test categorization of network errors"""
        error = ConnectionError("Connection failed")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.NETWORK_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 2.0
        assert result["max_retries"] == 5

    def test_timeout_error_categorization(self):
        """Test categorization of timeout errors"""
        # TimeoutError is caught by the network error check first
        error = TimeoutError("Operation timed out")
        result = categorize_task_error(error)

        assert (
            result["type"] == TaskErrorType.NETWORK_ERROR
        )  # TimeoutError is a subclass of OSError
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 2.0
        assert result["max_retries"] == 5

    def test_asyncio_timeout_error_categorization(self):
        """Test categorization of asyncio timeout errors"""
        error = TimeoutError("Async operation timed out")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.NETWORK_ERROR
        assert result["retryable"] is True

    def test_timeout_message_categorization(self):
        """Test categorization of errors with timeout in message"""
        error = Exception("Request timed out after 30 seconds")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.TIMEOUT_ERROR
        assert result["retryable"] is True

    def test_timed_out_message_categorization(self):
        """Test categorization of errors with 'timed out' in message"""
        error = Exception("Operation timed out")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.TIMEOUT_ERROR
        assert result["retryable"] is True

    def test_validation_error_categorization(self):
        """Test categorization of validation errors"""
        error = ValueError("Invalid input")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0

    def test_type_error_categorization(self):
        """Test categorization of type errors"""
        error = TypeError("Invalid type")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False

    def test_validation_message_categorization(self):
        """Test categorization of errors with validation in message"""
        error = Exception("Validation failed")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False

    def test_permission_error_categorization(self):
        """Test categorization of permission errors"""
        error = Exception("Permission denied")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PERMISSION_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0

    def test_unauthorized_error_categorization(self):
        """Test categorization of unauthorized errors"""
        error = Exception("Unauthorized access")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PERMISSION_ERROR
        assert result["retryable"] is False

    def test_resource_error_categorization(self):
        """Test categorization of resource errors"""
        error = Exception("Out of memory")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 3.0
        assert result["max_retries"] == 2

    def test_disk_error_categorization(self):
        """Test categorization of disk errors"""
        error = Exception("Disk space exceeded")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True

    def test_quota_error_categorization(self):
        """Test categorization of quota errors"""
        error = Exception("Quota exceeded")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True

    def test_external_service_error_categorization(self):
        """Test categorization of external service errors"""
        error = Exception("API rate limit exceeded")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 2.0
        assert result["max_retries"] == 4

    def test_service_error_categorization(self):
        """Test categorization of service errors"""
        error = Exception("Service unavailable")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True

    def test_third_party_error_categorization(self):
        """Test categorization of third-party errors"""
        error = Exception("Third-party service error")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True

    def test_programming_error_categorization(self):
        """Test categorization of programming errors"""
        error = AttributeError("Object has no attribute")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0

    def test_key_error_categorization(self):
        """Test categorization of key errors"""
        error = KeyError("Key not found")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False

    def test_index_error_categorization(self):
        """Test categorization of index errors"""
        error = IndexError("Index out of range")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False

    def test_import_error_categorization(self):
        """Test categorization of import errors"""
        error = ImportError("Module not found")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False

    def test_unknown_error_categorization(self):
        """Test categorization of unknown errors"""
        error = Exception("Some random error")
        result = categorize_task_error(error)

        assert result["type"] == TaskErrorType.UNKNOWN_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 1.0
        assert result["max_retries"] == 3


class TestTaskMetrics:
    """Test the TaskMetrics class"""

    def test_task_metrics_initialization(self):
        """Test TaskMetrics initialization"""
        metrics = TaskMetrics()

        assert metrics.tasks_started == 0
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.tasks_retried == 0
        assert metrics.total_processing_time == 0.0
        assert len(metrics.error_counts) == len(TaskErrorType)
        assert metrics.task_type_counts == {}
        assert metrics.last_activity is None

    def test_record_task_start(self):
        """Test recording task start"""
        metrics = TaskMetrics()

        with patch("services.background_tasks.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            metrics.record_task_start("test_task")

            assert metrics.tasks_started == 1
            assert metrics.task_type_counts["test_task"] == 1
            assert metrics.last_activity is not None

    def test_record_task_completion(self):
        """Test recording task completion"""
        metrics = TaskMetrics()

        with patch("services.background_tasks.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            metrics.record_task_completion(5.5)

            assert metrics.tasks_completed == 1
            assert metrics.total_processing_time == 5.5
            assert metrics.last_activity is not None

    def test_record_task_failure(self):
        """Test recording task failure"""
        metrics = TaskMetrics()

        with patch("services.background_tasks.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            metrics.record_task_failure(TaskErrorType.NETWORK_ERROR, 3.2)

            assert metrics.tasks_failed == 1
            assert metrics.error_counts["network_error"] == 1
            assert metrics.total_processing_time == 3.2
            assert metrics.last_activity is not None

    def test_record_task_retry(self):
        """Test recording task retry"""
        metrics = TaskMetrics()

        with patch("services.background_tasks.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            metrics.record_task_retry()

            assert metrics.tasks_retried == 1
            assert metrics.last_activity is not None

    def test_get_summary_no_tasks(self):
        """Test getting summary with no tasks"""
        metrics = TaskMetrics()
        summary = metrics.get_summary()

        assert summary["tasks_started"] == 0
        assert summary["tasks_completed"] == 0
        assert summary["tasks_failed"] == 0
        assert summary["tasks_retried"] == 0
        assert summary["success_rate"] == 0
        assert summary["avg_processing_time"] == 0
        assert "error_distribution" in summary
        assert "task_type_distribution" in summary
        assert summary["last_activity"] is None

    def test_get_summary_with_tasks(self):
        """Test getting summary with tasks"""
        metrics = TaskMetrics()

        # Add some test data
        metrics.tasks_started = 10
        metrics.tasks_completed = 8
        metrics.tasks_failed = 2
        metrics.tasks_retried = 1
        metrics.total_processing_time = 50.0
        metrics.error_counts["network_error"] = 1
        metrics.error_counts["validation_error"] = 1
        metrics.task_type_counts["test_task"] = 5
        metrics.task_type_counts["other_task"] = 5

        summary = metrics.get_summary()

        assert summary["tasks_started"] == 10
        assert summary["tasks_completed"] == 8
        assert summary["tasks_failed"] == 2
        assert summary["tasks_retried"] == 1
        assert summary["success_rate"] == 80.0  # 8/10 * 100
        assert summary["avg_processing_time"] == 5.0  # 50/10
        assert summary["error_distribution"]["network_error"] == 1
        assert summary["error_distribution"]["validation_error"] == 1
        assert summary["task_type_distribution"]["test_task"] == 5
        assert summary["task_type_distribution"]["other_task"] == 5


class TestGlobalTaskMetrics:
    """Test the global task_metrics instance"""

    def test_global_task_metrics_exists(self):
        """Test that global task_metrics instance exists"""
        assert task_metrics is not None
        assert isinstance(task_metrics, TaskMetrics)


class TestLogBackgroundTask:
    """Test the log_background_task decorator"""

    @patch("services.background_tasks.logger")
    @patch("services.background_tasks.task_metrics")
    @patch("services.background_tasks.datetime")
    @patch("services.background_tasks.uuid")
    def test_log_background_task_success(
        self, mock_uuid, mock_datetime, mock_metrics, mock_logger
    ):
        """Test successful background task execution"""
        # Mock UUID
        mock_uuid.uuid4.return_value.hex = "12345678"

        # Mock datetime
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 5)
        mock_datetime.utcnow.side_effect = [start_time, end_time]

        # Mock async function
        async def test_func():
            return "success"

        # Apply decorator
        decorated_func = log_background_task(test_func)

        # Test execution
        result = asyncio.run(decorated_func())

        assert result == "success"
        mock_metrics.record_task_start.assert_called_once_with("test_func")
        mock_metrics.record_task_completion.assert_called_once_with(5.0)
        mock_logger.info.assert_called()

    @patch("services.background_tasks.logger")
    @patch("services.background_tasks.task_metrics")
    @patch("services.background_tasks.datetime")
    @patch("services.background_tasks.uuid")
    def test_log_background_task_failure(
        self, mock_uuid, mock_datetime, mock_metrics, mock_logger
    ):
        """Test background task execution with failure"""
        # Mock UUID
        mock_uuid.uuid4.return_value.hex = "12345678"

        # Mock datetime
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 3)
        mock_datetime.utcnow.side_effect = [start_time, end_time]

        # Mock async function that raises an exception
        async def test_func():
            raise ValueError("Test error")

        # Apply decorator
        decorated_func = log_background_task(test_func)

        # Test execution
        with pytest.raises(ValueError, match="Test error"):
            asyncio.run(decorated_func())

        mock_metrics.record_task_start.assert_called_once_with("test_func")
        mock_metrics.record_task_failure.assert_called_once()
        mock_logger.error.assert_called_once()


class TestBackgroundTaskManager:
    """Test the BackgroundTaskManager class"""

    def test_background_task_manager_initialization(self):
        """Test BackgroundTaskManager initialization"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        assert manager.background_tasks == mock_background_tasks
        assert manager.active_tasks == {}

    @patch("services.background_tasks.uuid")
    def test_add_task(self, mock_uuid):
        """Test adding a task"""
        mock_uuid.uuid4.return_value.hex = "12345678"
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        def test_func():
            return "test"

        task_id = manager.add_task(test_func)

        assert task_id == "test_func_12345678"
        mock_background_tasks.add_task.assert_called_once()

    @patch("services.background_tasks.uuid")
    def test_add_task_with_retry(self, mock_uuid):
        """Test adding a task with retry"""
        mock_uuid.uuid4.return_value.hex = "12345678"
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        def test_func():
            return "test"

        task_id = manager.add_task_with_retry(test_func, max_retries=3, retry_delay=1.0)

        assert task_id == "test_func_12345678"
        mock_background_tasks.add_task.assert_called_once()

    @patch("services.background_tasks.uuid")
    def test_add_task_with_timeout(self, mock_uuid):
        """Test adding a task with timeout"""
        mock_uuid.uuid4.return_value.hex = "12345678"
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        def test_func():
            return "test"

        task_id = manager.add_task_with_timeout(test_func, timeout=300.0)

        assert task_id == "test_func_12345678"
        mock_background_tasks.add_task.assert_called_once()

    def test_get_metrics(self):
        """Test getting metrics"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        metrics = manager.get_metrics()

        assert isinstance(metrics, dict)
        assert "tasks_started" in metrics
        assert "tasks_completed" in metrics
        assert "tasks_failed" in metrics

    def test_get_health_status_healthy(self):
        """Test getting health status when healthy"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        # Mock the global task_metrics to simulate healthy state
        with patch("services.background_tasks.task_metrics") as mock_task_metrics:
            mock_task_metrics.get_summary.return_value = {
                "tasks_completed": 90,
                "tasks_failed": 10,
                "success_rate": 90.0,
                "last_activity": "2023-01-01T12:00:00",
            }

            health = manager.get_health_status()

            assert health["status"] == "healthy"
            assert health["error_rate"] == 10.0  # 10/(90+10) * 100
            assert health["success_rate"] == 90.0
            assert health["active_tasks"] == 0

    def test_get_health_status_degraded(self):
        """Test getting health status when degraded"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        # Mock the global task_metrics to simulate degraded state
        with patch("services.background_tasks.task_metrics") as mock_task_metrics:
            mock_task_metrics.get_summary.return_value = {
                "tasks_completed": 70,
                "tasks_failed": 30,
                "success_rate": 70.0,
                "last_activity": "2023-01-01T12:00:00",
            }

            health = manager.get_health_status()

            assert health["status"] == "degraded"
            assert health["error_rate"] == 30.0  # 30/(70+30) * 100

    def test_get_health_status_unhealthy(self):
        """Test getting health status when unhealthy"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        # Mock the global task_metrics to simulate unhealthy state
        with patch("services.background_tasks.task_metrics") as mock_task_metrics:
            mock_task_metrics.get_summary.return_value = {
                "tasks_completed": 40,
                "tasks_failed": 60,
                "success_rate": 40.0,
                "last_activity": "2023-01-01T12:00:00",
            }

            health = manager.get_health_status()

            assert health["status"] == "unhealthy"
            assert health["error_rate"] == 60.0  # 60/(40+60) * 100

    def test_get_health_status_no_tasks(self):
        """Test getting health status with no tasks"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        # Mock metrics to simulate no tasks
        with patch.object(manager, "get_metrics") as mock_get_metrics:
            mock_get_metrics.return_value = {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "success_rate": 0.0,
                "last_activity": None,
            }

            health = manager.get_health_status()

            assert health["status"] == "healthy"  # Default when no tasks
            assert health["error_rate"] == 0.0
            assert health["success_rate"] == 0.0


class TestBackgroundTaskManagerIntegration:
    """Test BackgroundTaskManager integration scenarios"""

    @patch("services.background_tasks.uuid")
    def test_manager_with_multiple_tasks(self, mock_uuid):
        """Test manager with multiple tasks"""
        mock_uuid.uuid4.return_value.hex = "12345678"
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        def task1():
            return "task1"

        def task2():
            return "task2"

        # Add multiple tasks
        task_id1 = manager.add_task(task1)
        task_id2 = manager.add_task_with_retry(task2)

        assert task_id1 == "task1_12345678"
        assert task_id2 == "task2_12345678"
        assert mock_background_tasks.add_task.call_count == 2

    def test_manager_metrics_integration(self):
        """Test manager metrics integration"""
        mock_background_tasks = MagicMock()
        manager = BackgroundTaskManager(mock_background_tasks)

        # Test that metrics are accessible
        metrics = manager.get_metrics()
        health = manager.get_health_status()

        assert isinstance(metrics, dict)
        assert isinstance(health, dict)
        assert "metrics" in health
