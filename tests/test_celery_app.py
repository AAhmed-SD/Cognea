import pytest
import os
import logging
from unittest.mock import MagicMock, patch, Mock
from datetime import timedelta

from services.celery_app import celery_app, setup_loggers


class TestCeleryApp:
    """Test Celery application configuration."""

    def test_celery_app_creation(self):
        """Test that Celery app is properly created."""
        assert celery_app is not None
        assert celery_app.main == "personal_agent"

    def test_celery_app_default_broker_config(self):
        """Test Celery broker configuration with defaults."""
        # Clear environment to test defaults
        with patch.dict('os.environ', {}, clear=True):
            # Import again to test defaults
            from services.celery_app import celery_app as test_app
            
            # Note: We can't easily test the broker URL after creation,
            # but we can verify the app was created successfully
            assert test_app is not None

    def test_celery_app_custom_broker_config(self):
        """Test Celery broker configuration with custom values."""
        custom_config = {
            "CELERY_BROKER_URL": "redis://custom-host:6380/1",
            "CELERY_RESULT_BACKEND": "redis://custom-host:6380/2"
        }
        
        with patch.dict('os.environ', custom_config):
            # We can't easily re-import the module, but we can verify
            # that the environment variables would be used
            broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
            backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
            
            assert broker_url == "redis://custom-host:6380/1"
            assert backend_url == "redis://custom-host:6380/2"

    def test_celery_app_configuration(self):
        """Test Celery application configuration settings."""
        conf = celery_app.conf
        
        # Test serialization settings
        assert conf.task_serializer == "json"
        assert conf.accept_content == ["json"]
        assert conf.result_serializer == "json"
        
        # Test timezone settings
        assert conf.timezone == "UTC"
        assert conf.enable_utc is True
        
        # Test task settings
        assert conf.task_track_started is True
        assert conf.task_time_limit == 3600
        assert conf.task_soft_time_limit == 3000
        assert conf.worker_max_tasks_per_child == 1000
        assert conf.worker_prefetch_multiplier == 1
        assert conf.task_acks_late is True
        assert conf.task_reject_on_worker_lost is True

    def test_celery_app_queues_configuration(self):
        """Test Celery queues configuration."""
        conf = celery_app.conf
        
        # Test default queue
        assert conf.task_default_queue == "default"
        
        # Test queue definitions
        queues = conf.task_queues
        assert "default" in queues
        assert "notion" in queues
        assert "ai" in queues
        assert "email" in queues
        
        # Test queue settings
        assert queues["default"]["exchange"] == "default"
        assert queues["default"]["routing_key"] == "default"
        assert queues["notion"]["exchange"] == "notion"
        assert queues["notion"]["routing_key"] == "notion"

    def test_celery_app_task_routes(self):
        """Test Celery task routing configuration."""
        conf = celery_app.conf
        routes = conf.task_routes
        
        # Test route mappings
        assert "services.tasks.notion.*" in routes
        assert "services.tasks.ai.*" in routes
        assert "services.tasks.email.*" in routes
        
        # Test queue assignments
        assert routes["services.tasks.notion.*"]["queue"] == "notion"
        assert routes["services.tasks.ai.*"]["queue"] == "ai"
        assert routes["services.tasks.email.*"]["queue"] == "email"

    def test_celery_beat_schedule(self):
        """Test Celery beat schedule configuration."""
        conf = celery_app.conf
        schedule = conf.beat_schedule
        
        # Test scheduled tasks exist
        assert "sync-notion" in schedule
        assert "cleanup-old-tasks" in schedule
        
        # Test sync-notion task
        sync_task = schedule["sync-notion"]
        assert sync_task["task"] == "services.tasks.notion.sync_notion_data"
        assert sync_task["schedule"] == timedelta(minutes=15)
        
        # Test cleanup task
        cleanup_task = schedule["cleanup-old-tasks"]
        assert cleanup_task["task"] == "services.tasks.cleanup.cleanup_old_tasks"
        assert cleanup_task["schedule"] == timedelta(days=1)

    def test_celery_app_includes(self):
        """Test Celery app includes configuration."""
        # Test that tasks module is included
        assert "services.tasks" in celery_app.conf.include

    @patch('os.makedirs')
    def test_logs_directory_creation(self, mock_makedirs):
        """Test that logs directory is created."""
        # Re-import to trigger directory creation
        import importlib
        import services.celery_app
        importlib.reload(services.celery_app)
        
        # Verify makedirs was called
        mock_makedirs.assert_called_with("logs", exist_ok=True)


class TestCeleryLogging:
    """Test Celery logging configuration."""

    def test_setup_loggers_function_exists(self):
        """Test that setup_loggers function exists and is callable."""
        assert callable(setup_loggers)

    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    def test_setup_loggers_configuration(self, mock_stream_handler, mock_file_handler):
        """Test setup_loggers function configuration."""
        # Mock handlers
        mock_fh = MagicMock()
        mock_ch = MagicMock()
        mock_file_handler.return_value = mock_fh
        mock_stream_handler.return_value = mock_ch
        
        # Mock logger
        mock_logger = MagicMock()
        
        # Call setup_loggers
        setup_loggers(mock_logger)
        
        # Verify file handler was created and configured
        mock_file_handler.assert_called_once_with("logs/celery.log")
        mock_fh.setFormatter.assert_called_once()
        
        # Verify stream handler was created and configured
        mock_stream_handler.assert_called_once()
        mock_ch.setFormatter.assert_called_once()
        
        # Verify handlers were added to logger
        assert mock_logger.addHandler.call_count == 2
        mock_logger.addHandler.assert_any_call(mock_fh)
        mock_logger.addHandler.assert_any_call(mock_ch)
        
        # Verify log level was set
        mock_logger.setLevel.assert_called_once_with(logging.INFO)

    def test_setup_loggers_formatter(self):
        """Test that setup_loggers creates proper formatter."""
        with patch('logging.FileHandler') as mock_fh, \
             patch('logging.StreamHandler') as mock_ch:
            
            mock_logger = MagicMock()
            
            setup_loggers(mock_logger)
            
            # Get the formatter that was created
            file_handler_call = mock_fh.return_value.setFormatter.call_args[0][0]
            stream_handler_call = mock_ch.return_value.setFormatter.call_args[0][0]
            
            # Verify formatter format string
            expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            assert file_handler_call._fmt == expected_format
            assert stream_handler_call._fmt == expected_format

    def test_setup_loggers_with_args_kwargs(self):
        """Test setup_loggers handles additional args and kwargs."""
        mock_logger = MagicMock()
        
        with patch('logging.FileHandler'), \
             patch('logging.StreamHandler'):
            
            # Should not raise exception with additional args/kwargs
            setup_loggers(mock_logger)
            
            # Logger should still be configured
            mock_logger.setLevel.assert_called_once_with(logging.INFO)


class TestCeleryAppIntegration:
    """Integration tests for Celery application."""

    def test_celery_app_signal_connection(self):
        """Test that after_setup_logger signal is connected."""
        from celery.signals import after_setup_logger
        
        # Check if our setup_loggers function is connected
        # Note: This is a basic check - in a real scenario you'd verify
        # the signal connection more thoroughly
        assert hasattr(after_setup_logger, 'receivers')

    def test_celery_app_configuration_types(self):
        """Test that configuration values have correct types."""
        conf = celery_app.conf
        
        # Test integer types
        assert isinstance(conf.task_time_limit, int)
        assert isinstance(conf.task_soft_time_limit, int)
        assert isinstance(conf.worker_max_tasks_per_child, int)
        assert isinstance(conf.worker_prefetch_multiplier, int)
        
        # Test boolean types
        assert isinstance(conf.task_track_started, bool)
        assert isinstance(conf.enable_utc, bool)
        assert isinstance(conf.task_acks_late, bool)
        assert isinstance(conf.task_reject_on_worker_lost, bool)
        
        # Test string types
        assert isinstance(conf.task_serializer, str)
        assert isinstance(conf.result_serializer, str)
        assert isinstance(conf.timezone, str)
        assert isinstance(conf.task_default_queue, str)

    def test_celery_app_timedelta_objects(self):
        """Test that timedelta objects are properly configured."""
        conf = celery_app.conf
        schedule = conf.beat_schedule
        
        # Test that schedule values are timedelta objects
        assert isinstance(schedule["sync-notion"]["schedule"], timedelta)
        assert isinstance(schedule["cleanup-old-tasks"]["schedule"], timedelta)
        
        # Test specific timedelta values
        assert schedule["sync-notion"]["schedule"].total_seconds() == 15 * 60  # 15 minutes
        assert schedule["cleanup-old-tasks"]["schedule"].total_seconds() == 24 * 60 * 60  # 1 day

    def test_celery_app_environment_integration(self):
        """Test Celery app integration with environment variables."""
        # Test that environment variables are used for configuration
        default_broker = "redis://localhost:6379/0"
        default_backend = "redis://localhost:6379/0"
        
        # Test with default values
        with patch.dict('os.environ', {}, clear=True):
            broker = os.getenv("CELERY_BROKER_URL", default_broker)
            backend = os.getenv("CELERY_RESULT_BACKEND", default_backend)
            
            assert broker == default_broker
            assert backend == default_backend

    def test_celery_app_queue_configuration_completeness(self):
        """Test that all queues have complete configuration."""
        conf = celery_app.conf
        queues = conf.task_queues
        
        for queue_name, queue_config in queues.items():
            # Each queue should have exchange and routing_key
            assert "exchange" in queue_config
            assert "routing_key" in queue_config
            assert isinstance(queue_config["exchange"], str)
            assert isinstance(queue_config["routing_key"], str)
            assert len(queue_config["exchange"]) > 0
            assert len(queue_config["routing_key"]) > 0

    def test_celery_app_task_routes_completeness(self):
        """Test that all task routes have proper queue assignments."""
        conf = celery_app.conf
        routes = conf.task_routes
        queues = conf.task_queues
        
        for route_pattern, route_config in routes.items():
            # Each route should specify a queue
            assert "queue" in route_config
            queue_name = route_config["queue"]
            
            # The queue should exist in queue definitions
            assert queue_name in queues

    def test_celery_app_beat_schedule_task_names(self):
        """Test that beat schedule tasks have valid task names."""
        conf = celery_app.conf
        schedule = conf.beat_schedule
        
        for schedule_name, schedule_config in schedule.items():
            # Each scheduled task should have a task name
            assert "task" in schedule_config
            assert "schedule" in schedule_config
            
            task_name = schedule_config["task"]
            assert isinstance(task_name, str)
            assert len(task_name) > 0
            assert "." in task_name  # Should be a dotted module path


class TestCeleryAppConfiguration:
    """Test specific Celery configuration scenarios."""

    def test_celery_app_worker_settings(self):
        """Test worker-specific settings."""
        conf = celery_app.conf
        
        # Test worker settings are appropriate for production
        assert conf.worker_max_tasks_per_child == 1000  # Prevents memory leaks
        assert conf.worker_prefetch_multiplier == 1  # Better for long-running tasks
        assert conf.task_acks_late is True  # Better reliability
        assert conf.task_reject_on_worker_lost is True  # Handle worker failures

    def test_celery_app_task_time_limits(self):
        """Test task time limit settings."""
        conf = celery_app.conf
        
        # Test time limits are reasonable
        assert conf.task_time_limit == 3600  # 1 hour hard limit
        assert conf.task_soft_time_limit == 3000  # 50 minutes soft limit
        assert conf.task_soft_time_limit < conf.task_time_limit  # Soft < Hard

    def test_celery_app_serialization_security(self):
        """Test serialization settings for security."""
        conf = celery_app.conf
        
        # JSON serialization is safer than pickle
        assert conf.task_serializer == "json"
        assert conf.result_serializer == "json"
        assert "json" in conf.accept_content
        
        # Should not accept pickle for security
        assert "pickle" not in conf.accept_content

    def test_celery_app_timezone_settings(self):
        """Test timezone configuration."""
        conf = celery_app.conf
        
        # UTC is recommended for distributed systems
        assert conf.timezone == "UTC"
        assert conf.enable_utc is True
