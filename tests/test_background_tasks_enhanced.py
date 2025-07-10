import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import BackgroundTasks

from services.background_tasks import (
    TaskErrorType, TaskStatus, categorize_task_error, TaskMetrics,
    task_metrics, log_background_task, BackgroundTaskManager
)


class TestTaskErrorType:
    """Test TaskErrorType enum."""
    
    def test_task_error_type_values(self):
        """Test TaskErrorType enum values."""
        assert TaskErrorType.NETWORK_ERROR.value == "network_error"
        assert TaskErrorType.TIMEOUT_ERROR.value == "timeout_error"
        assert TaskErrorType.VALIDATION_ERROR.value == "validation_error"
        assert TaskErrorType.PERMISSION_ERROR.value == "permission_error"
        assert TaskErrorType.RESOURCE_ERROR.value == "resource_error"
        assert TaskErrorType.EXTERNAL_SERVICE_ERROR.value == "external_service_error"
        assert TaskErrorType.PROGRAMMING_ERROR.value == "programming_error"
        assert TaskErrorType.UNKNOWN_ERROR.value == "unknown_error"


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRY.value == "retry"


class TestCategorizeTaskError:
    """Test error categorization function."""
    
    def test_network_error_categorization(self):
        """Test network error categorization."""
        error = ConnectionError("Connection failed")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.NETWORK_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 2.0
        assert result["max_retries"] == 5
    
    def test_timeout_error_categorization(self):
        """Test timeout error categorization."""
        error = TimeoutError("Request timed out")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.NETWORK_ERROR  # TimeoutError is treated as network error
        assert result["retryable"] is True
    
    def test_asyncio_timeout_error_categorization(self):
        """Test asyncio timeout error categorization."""
        error = asyncio.TimeoutError("Async operation timed out")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.NETWORK_ERROR
        assert result["retryable"] is True
    
    def test_timeout_message_categorization(self):
        """Test timeout message categorization."""
        error = Exception("Operation timeout occurred")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.TIMEOUT_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 1.5
        assert result["max_retries"] == 3
    
    def test_timed_out_message_categorization(self):
        """Test 'timed out' message categorization."""
        error = Exception("Request timed out after 30 seconds")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.TIMEOUT_ERROR
        assert result["retryable"] is True
    
    def test_validation_error_categorization(self):
        """Test validation error categorization."""
        error = ValueError("Invalid input data")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0
    
    def test_type_error_categorization(self):
        """Test type error categorization."""
        error = TypeError("Expected string, got int")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False
    
    def test_validation_message_categorization(self):
        """Test validation message categorization."""
        error = Exception("Validation failed for field")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.VALIDATION_ERROR
        assert result["retryable"] is False
    
    def test_permission_error_categorization(self):
        """Test permission error categorization."""
        error = Exception("Permission denied")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PERMISSION_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0
    
    def test_unauthorized_error_categorization(self):
        """Test unauthorized error categorization."""
        error = Exception("Unauthorized access")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PERMISSION_ERROR
        assert result["retryable"] is False
    
    def test_resource_error_categorization(self):
        """Test resource error categorization."""
        error = Exception("Out of memory")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 3.0
        assert result["max_retries"] == 2
    
    def test_disk_error_categorization(self):
        """Test disk error categorization."""
        error = Exception("Disk space quota exceeded")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True
    
    def test_quota_error_categorization(self):
        """Test quota error categorization."""
        error = Exception("Resource quota exceeded")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.RESOURCE_ERROR
        assert result["retryable"] is True
    
    def test_external_service_error_categorization(self):
        """Test external service error categorization."""
        error = Exception("API service unavailable")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 2.0
        assert result["max_retries"] == 4
    
    def test_service_error_categorization(self):
        """Test service error categorization."""
        error = Exception("External service error")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True
    
    def test_third_party_error_categorization(self):
        """Test third-party error categorization."""
        error = Exception("Third-party integration failed")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.EXTERNAL_SERVICE_ERROR
        assert result["retryable"] is True
    
    def test_programming_error_categorization(self):
        """Test programming error categorization."""
        error = AttributeError("'NoneType' object has no attribute 'value'")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False
        assert result["max_retries"] == 0
    
    def test_key_error_categorization(self):
        """Test key error categorization."""
        error = KeyError("missing_key")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False
    
    def test_index_error_categorization(self):
        """Test index error categorization."""
        error = IndexError("list index out of range")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False
    
    def test_import_error_categorization(self):
        """Test import error categorization."""
        error = ImportError("No module named 'missing_module'")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.PROGRAMMING_ERROR
        assert result["retryable"] is False
    
    def test_unknown_error_categorization(self):
        """Test unknown error categorization."""
        error = Exception("Some unexpected error")
        result = categorize_task_error(error)
        
        assert result["type"] == TaskErrorType.UNKNOWN_ERROR
        assert result["retryable"] is True
        assert result["retry_delay_multiplier"] == 1.0
        assert result["max_retries"] == 3


class TestTaskMetrics:
    """Test TaskMetrics class."""
    
    @pytest.fixture
    def metrics(self):
        """Create a fresh TaskMetrics instance."""
        return TaskMetrics()
    
    def test_task_metrics_initialization(self, metrics):
        """Test TaskMetrics initialization."""
        assert metrics.tasks_started == 0
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.tasks_retried == 0
        assert metrics.total_processing_time == 0.0
        assert len(metrics.error_counts) == len(TaskErrorType)
        assert metrics.task_type_counts == {}
        assert metrics.last_activity is None
    
    def test_record_task_start(self, metrics):
        """Test recording task start."""
        metrics.record_task_start("test_task")
        
        assert metrics.tasks_started == 1
        assert metrics.task_type_counts["test_task"] == 1
        assert metrics.last_activity is not None
    
    def test_record_task_completion(self, metrics):
        """Test recording task completion."""
        processing_time = 1.5
        metrics.record_task_completion(processing_time)
        
        assert metrics.tasks_completed == 1
        assert metrics.total_processing_time == processing_time
        assert metrics.last_activity is not None
    
    def test_record_task_failure(self, metrics):
        """Test recording task failure."""
        processing_time = 2.0
        error_type = TaskErrorType.NETWORK_ERROR
        
        metrics.record_task_failure(error_type, processing_time)
        
        assert metrics.tasks_failed == 1
        assert metrics.error_counts[error_type.value] == 1
        assert metrics.total_processing_time == processing_time
        assert metrics.last_activity is not None
    
    def test_record_task_retry(self, metrics):
        """Test recording task retry."""
        metrics.record_task_retry()
        
        assert metrics.tasks_retried == 1
        assert metrics.last_activity is not None
    
    def test_get_summary_no_tasks(self, metrics):
        """Test getting summary with no tasks."""
        summary = metrics.get_summary()
        
        assert summary["tasks_started"] == 0
        assert summary["tasks_completed"] == 0
        assert summary["tasks_failed"] == 0
        assert summary["tasks_retried"] == 0
        assert summary["success_rate"] == 0
        assert summary["avg_processing_time"] == 0
        assert isinstance(summary["error_distribution"], dict)
        assert isinstance(summary["task_type_distribution"], dict)
    
    def test_get_summary_with_tasks(self, metrics):
        """Test getting summary with tasks."""
        # Record some task activity
        metrics.record_task_start("task1")
        metrics.record_task_completion(1.0)
        metrics.record_task_start("task2")
        metrics.record_task_failure(TaskErrorType.TIMEOUT_ERROR, 2.0)
        metrics.record_task_retry()
        
        summary = metrics.get_summary()
        
        assert summary["tasks_started"] == 2
        assert summary["tasks_completed"] == 1
        assert summary["tasks_failed"] == 1
        assert summary["tasks_retried"] == 1
        assert summary["success_rate"] == 50.0  # 1 completed out of 2 total
        assert summary["avg_processing_time"] == 1.5  # (1.0 + 2.0) / 2
        assert summary["error_distribution"][TaskErrorType.TIMEOUT_ERROR.value] == 1


class TestGlobalTaskMetrics:
    """Test global task metrics instance."""
    
    def test_global_task_metrics_exists(self):
        """Test that global task_metrics instance exists."""
        assert task_metrics is not None
        assert isinstance(task_metrics, TaskMetrics)


class TestLogBackgroundTaskDecorator:
    """Test log_background_task decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_logs_successful_task(self):
        """Test decorator logs successful task execution."""
        @log_background_task
        async def test_task():
            return "success"
        
        with patch('services.background_tasks.logger') as mock_logger:
            result = await test_task()
            
            assert result == "success"
            assert mock_logger.info.call_count == 2  # Start and completion logs
    
    @pytest.mark.asyncio
    async def test_decorator_logs_failed_task(self):
        """Test decorator logs failed task execution."""
        @log_background_task
        async def failing_task():
            raise ValueError("Task failed")
        
        with patch('services.background_tasks.logger') as mock_logger:
            with pytest.raises(ValueError, match="Task failed"):
                await failing_task()
            
            mock_logger.info.assert_called_once()  # Start log only
            mock_logger.error.assert_called_once()  # Error log
    
    @pytest.mark.asyncio
    async def test_decorator_updates_metrics(self):
        """Test decorator updates task metrics."""
        initial_started = task_metrics.tasks_started
        initial_completed = task_metrics.tasks_completed
        
        @log_background_task
        async def test_task():
            return "success"
        
        await test_task()
        
        assert task_metrics.tasks_started == initial_started + 1
        assert task_metrics.tasks_completed == initial_completed + 1


class TestBackgroundTaskManager:
    """Test BackgroundTaskManager class."""
    
    @pytest.fixture
    def background_tasks(self):
        """Create BackgroundTasks instance."""
        return BackgroundTasks()
    
    @pytest.fixture
    def task_manager(self, background_tasks):
        """Create BackgroundTaskManager instance."""
        return BackgroundTaskManager(background_tasks)
    
    def test_manager_initialization(self, task_manager, background_tasks):
        """Test BackgroundTaskManager initialization."""
        assert task_manager.background_tasks == background_tasks
        assert task_manager.active_tasks == {}
    
    def test_add_task(self, task_manager):
        """Test adding a task."""
        def test_task():
            return "task executed"
        
        task_id = task_manager.add_task(test_task)
        
        assert isinstance(task_id, str)
        assert "test_task" in task_id
    
    def test_add_task_with_retry(self, task_manager):
        """Test adding a task with retry."""
        def test_task():
            return "task executed"
        
        task_id = task_manager.add_task_with_retry(test_task, max_retries=5, retry_delay=2.0)
        
        assert isinstance(task_id, str)
        assert "test_task" in task_id
    
    def test_add_task_with_timeout(self, task_manager):
        """Test adding a task with timeout."""
        def test_task():
            return "task executed"
        
        task_id = task_manager.add_task_with_timeout(test_task, timeout=10.0)
        
        assert isinstance(task_id, str)
        assert "test_task" in task_id
    
    def test_get_metrics(self, task_manager):
        """Test getting task metrics."""
        metrics = task_manager.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "tasks_started" in metrics
        assert "tasks_completed" in metrics
        assert "tasks_failed" in metrics
        assert "success_rate" in metrics
    
    def test_get_health_status_healthy(self, task_manager):
        """Test getting healthy status."""
        # Mock metrics for healthy status
        with patch.object(task_metrics, 'get_summary') as mock_summary:
            mock_summary.return_value = {
                "tasks_completed": 90,
                "tasks_failed": 10,
                "success_rate": 90.0,
                "last_activity": datetime.utcnow().isoformat()
            }
            
            health = task_manager.get_health_status()
            
            assert health["status"] == "healthy"
            assert health["error_rate"] == 10.0
            assert health["success_rate"] == 90.0
            assert "metrics" in health
    
    def test_get_health_status_degraded(self, task_manager):
        """Test getting degraded status."""
        # Mock metrics for degraded status (error rate > 20%)
        with patch.object(task_metrics, 'get_summary') as mock_summary:
            mock_summary.return_value = {
                "tasks_completed": 70,
                "tasks_failed": 30,
                "success_rate": 70.0,
                "last_activity": datetime.utcnow().isoformat()
            }
            
            health = task_manager.get_health_status()
            
            assert health["status"] == "degraded"
            assert health["error_rate"] == 30.0
    
    def test_get_health_status_unhealthy(self, task_manager):
        """Test getting unhealthy status."""
        # Mock metrics for unhealthy status (error rate > 50%)
        with patch.object(task_metrics, 'get_summary') as mock_summary:
            mock_summary.return_value = {
                "tasks_completed": 40,
                "tasks_failed": 60,
                "success_rate": 40.0,
                "last_activity": datetime.utcnow().isoformat()
            }
            
            health = task_manager.get_health_status()
            
            assert health["status"] == "unhealthy"
            assert health["error_rate"] == 60.0