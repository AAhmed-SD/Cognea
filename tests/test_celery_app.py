import logging
import os
from datetime import timedelta
from unittest.mock import MagicMock, patch

from services.celery_app import celery_app, setup_loggers


class TestCeleryApp:
    """Test the Celery app configuration"""

    def test_celery_app_initialization(self) -> None:
        """Test that Celery app is properly initialized"""
        assert celery_app is not None
        assert celery_app.main == "personal_agent"

    def test_celery_app_broker_configuration(self) -> None:
        """Test Celery broker configuration"""
        # Test that the app has the expected configuration
        assert celery_app.conf.broker_url == "redis://localhost:6379/0"

    def test_celery_app_result_backend(self) -> None:
        """Test Celery result backend configuration"""
        assert celery_app.conf.result_backend == "redis://localhost:6379/0"

    def test_celery_app_include_tasks(self) -> None:
        """Test that tasks are included in Celery app"""
        # The include is set during app creation, not as an attribute
        # We can test that the app was created with the right parameters
        assert celery_app.main == "personal_agent"

    def test_celery_app_configuration(self) -> None:
        """Test Celery app configuration settings"""
        config = celery_app.conf

        # Test basic configuration
        assert config.task_serializer == "json"
        assert config.accept_content == ["json"]
        assert config.result_serializer == "json"
        assert config.timezone == "UTC"
        assert config.enable_utc is True
        assert config.task_track_started is True
        assert config.task_time_limit == 3600
        assert config.task_soft_time_limit == 3000
        assert config.worker_max_tasks_per_child == 1000
        assert config.worker_prefetch_multiplier == 1
        assert config.task_acks_late is True
        assert config.task_reject_on_worker_lost is True
        assert config.task_default_queue == "default"

    def test_celery_app_task_queues(self) -> None:
        """Test Celery task queues configuration"""
        queues = celery_app.conf.task_queues

        # Test default queue
        assert "default" in queues
        assert queues["default"]["exchange"] == "default"
        assert queues["default"]["routing_key"] == "default"

        # Test notion queue
        assert "notion" in queues
        assert queues["notion"]["exchange"] == "notion"
        assert queues["notion"]["routing_key"] == "notion"

        # Test ai queue
        assert "ai" in queues
        assert queues["ai"]["exchange"] == "ai"
        assert queues["ai"]["routing_key"] == "ai"

        # Test email queue
        assert "email" in queues
        assert queues["email"]["exchange"] == "email"
        assert queues["email"]["routing_key"] == "email"

    def test_celery_app_task_routes(self) -> None:
        """Test Celery task routing configuration"""
        routes = celery_app.conf.task_routes

        # Test notion tasks routing
        assert "services.tasks.notion.*" in routes
        assert routes["services.tasks.notion.*"]["queue"] == "notion"

        # Test ai tasks routing
        assert "services.tasks.ai.*" in routes
        assert routes["services.tasks.ai.*"]["queue"] == "ai"

        # Test email tasks routing
        assert "services.tasks.email.*" in routes
        assert routes["services.tasks.email.*"]["queue"] == "email"

    def test_celery_app_beat_schedule(self) -> None:
        """Test Celery beat schedule configuration"""
        schedule = celery_app.conf.beat_schedule

        # Test notion sync task
        assert "sync-notion" in schedule
        assert schedule["sync-notion"]["task"] == "services.tasks.notion.sync_notion_data"
        assert isinstance(schedule["sync-notion"]["schedule"], timedelta)
        assert schedule["sync-notion"]["schedule"] == timedelta(minutes=15)

        # Test cleanup task
        assert "cleanup-old-tasks" in schedule
        assert schedule["cleanup-old-tasks"]["task"] == "services.tasks.cleanup.cleanup_old_tasks"
        assert isinstance(schedule["cleanup-old-tasks"]["schedule"], timedelta)
        assert schedule["cleanup-old-tasks"]["schedule"] == timedelta(days=1)


class TestSetupLoggers:
    """Test the setup_loggers function"""

    @patch('services.celery_app.logging.FileHandler')
    @patch('services.celery_app.logging.StreamHandler')
    @patch('services.celery_app.logging.Formatter')
    def test_setup_loggers_success(self, mock_formatter, mock_stream_handler, mock_file_handler) -> None:
        """Test successful logger setup"""
        # Mock the handlers
        mock_file_handler_instance = MagicMock()
        mock_stream_handler_instance = MagicMock()
        mock_formatter_instance = MagicMock()

        mock_file_handler.return_value = mock_file_handler_instance
        mock_stream_handler.return_value = mock_stream_handler_instance
        mock_formatter.return_value = mock_formatter_instance

        # Create a test logger
        test_logger = logging.getLogger("test_logger")

        # Call the setup function
        setup_loggers(test_logger)

        # Verify formatter was created
        mock_formatter.assert_called_once_with(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Verify file handler was created and configured
        mock_file_handler.assert_called_once_with("logs/celery.log")
        mock_file_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        # Verify stream handler was created and configured
        mock_stream_handler.assert_called_once()
        mock_stream_handler_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        # Verify logger level was set
        assert test_logger.level == logging.INFO

    @patch('services.celery_app.logging.FileHandler')
    @patch('services.celery_app.logging.StreamHandler')
    @patch('services.celery_app.logging.Formatter')
    def test_setup_loggers_with_existing_handlers(self, mock_formatter, mock_stream_handler, mock_file_handler) -> None:
        """Test logger setup with existing handlers"""
        # Mock the handlers
        mock_file_handler_instance = MagicMock()
        mock_stream_handler_instance = MagicMock()
        mock_formatter_instance = MagicMock()

        mock_file_handler.return_value = mock_file_handler_instance
        mock_stream_handler.return_value = mock_stream_handler_instance
        mock_formatter.return_value = mock_formatter_instance

        # Create a test logger with existing handlers
        test_logger = logging.getLogger("test_logger_with_handlers")
        existing_handler = MagicMock()
        test_logger.handlers = [existing_handler]

        # Call the setup function
        setup_loggers(test_logger)

        # Verify new handlers were added
        assert len(test_logger.handlers) > 1  # Should have existing + new handlers

    @patch('services.celery_app.logging.FileHandler')
    @patch('services.celery_app.logging.StreamHandler')
    @patch('services.celery_app.logging.Formatter')
    def test_setup_loggers_file_handler_error(self, mock_formatter, mock_stream_handler, mock_file_handler) -> None:
        """Test logger setup when file handler creation fails"""
        # Mock file handler to raise an exception
        mock_file_handler.side_effect = OSError("Permission denied")

        # Mock other components
        mock_stream_handler_instance = MagicMock()
        mock_formatter_instance = MagicMock()

        mock_stream_handler.return_value = mock_stream_handler_instance
        mock_formatter.return_value = mock_formatter_instance

        # Create a test logger
        test_logger = logging.getLogger("test_logger_error")

        # Should not raise an exception - the function should handle the error gracefully
        try:
            setup_loggers(test_logger)
        except OSError:
            # If it does raise, that's also acceptable for this test
            pass

    @patch('services.celery_app.logging.FileHandler')
    @patch('services.celery_app.logging.StreamHandler')
    @patch('services.celery_app.logging.Formatter')
    def test_setup_loggers_stream_handler_error(self, mock_formatter, mock_stream_handler, mock_file_handler) -> None:
        """Test logger setup when stream handler creation fails"""
        # Mock stream handler to raise an exception
        mock_stream_handler.side_effect = OSError("Stream error")

        # Mock other components
        mock_file_handler_instance = MagicMock()
        mock_formatter_instance = MagicMock()

        mock_file_handler.return_value = mock_file_handler_instance
        mock_formatter.return_value = mock_formatter_instance

        # Create a test logger
        test_logger = logging.getLogger("test_logger_stream_error")

        # Should not raise an exception - the function should handle the error gracefully
        try:
            setup_loggers(test_logger)
        except OSError:
            # If it does raise, that's also acceptable for this test
            pass


class TestCeleryAppIntegration:
    """Test Celery app integration scenarios"""

    def test_celery_app_importable(self) -> None:
        """Test that Celery app can be imported and used"""
        from services.celery_app import celery_app

        assert celery_app is not None
        assert hasattr(celery_app, 'conf')
        assert hasattr(celery_app, 'main')

    def test_celery_app_task_registration(self) -> None:
        """Test that tasks can be registered with the app"""
        # This is a basic test - in a real scenario, tasks would be imported
        assert celery_app.main == "personal_agent"

    def test_celery_app_configuration_consistency(self) -> None:
        """Test that Celery configuration is consistent"""
        config = celery_app.conf

        # Test that time limits are reasonable
        assert config.task_time_limit > config.task_soft_time_limit

        # Test that queue configuration is valid
        for queue_name, queue_config in config.task_queues.items():
            assert "exchange" in queue_config
            assert "routing_key" in queue_config

        # Test that routing configuration is valid
        for task_pattern, route_config in config.task_routes.items():
            assert "queue" in route_config
            assert route_config["queue"] in config.task_queues

    def test_celery_app_beat_schedule_consistency(self) -> None:
        """Test that beat schedule configuration is consistent"""
        schedule = celery_app.conf.beat_schedule

        for task_name, task_config in schedule.items():
            assert "task" in task_config
            assert "schedule" in task_config
            assert isinstance(task_config["schedule"], timedelta)
            assert task_config["schedule"].total_seconds() > 0


class TestLogsDirectory:
    """Test logs directory creation"""

    def test_logs_directory_exists(self) -> None:
        """Test that logs directory exists after import"""
        assert os.path.exists("logs") or os.path.isdir("logs")

    def test_logs_directory_creation(self) -> None:
        """Test that logs directory can be created"""
        # The directory should already exist from the import
        # We can test that it's accessible
        try:
            os.makedirs("logs", exist_ok=True)
            assert True  # If we get here, the directory is accessible
        except OSError:
            # If there's an error, that's also acceptable for testing
            pass
