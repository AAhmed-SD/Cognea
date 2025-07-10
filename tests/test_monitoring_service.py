import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC
from fastapi import Request, Response

from services.monitoring import MonitoringService, monitoring_service, get_monitoring_service


class TestMonitoringService:
    """Test monitoring service functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.client = MagicMock()
        return mock_client

    @pytest.fixture
    def monitoring_svc(self, mock_redis_client):
        """Create monitoring service with mocked Redis."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            return MonitoringService()

    def test_monitoring_service_init(self, monitoring_svc):
        """Test MonitoringService initialization."""
        assert monitoring_svc.redis_client is not None
        assert isinstance(monitoring_svc.start_time, datetime)

    def test_log_request_success(self, monitoring_svc):
        """Test logging successful HTTP request."""
        # Mock request and response
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.headers.get.return_value = "test-user-agent"
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        duration = 0.5

        with patch('services.monitoring.REQUEST_COUNT') as mock_counter, \
             patch('services.monitoring.REQUEST_DURATION') as mock_histogram:
            
            monitoring_svc.log_request(mock_request, mock_response, duration)

            # Verify Prometheus metrics
            mock_counter.labels.assert_called_with(method="GET", endpoint="/api/test", status=200)
            mock_counter.labels.return_value.inc.assert_called_once()
            mock_histogram.observe.assert_called_with(duration)

            # Verify Redis logging
            monitoring_svc.redis_client.client.lpush.assert_called_once()
            monitoring_svc.redis_client.client.expire.assert_called_once()

    def test_log_request_redis_disconnected(self, mock_redis_client):
        """Test logging request when Redis is disconnected."""
        mock_redis_client.is_connected.return_value = False
        
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            monitoring_svc = MonitoringService()

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 201

        with patch('services.monitoring.REQUEST_COUNT'), \
             patch('services.monitoring.REQUEST_DURATION'):
            
            monitoring_svc.log_request(mock_request, mock_response, 0.3)

            # Redis should not be called
            mock_redis_client.client.lpush.assert_not_called()

    def test_log_error(self, monitoring_svc):
        """Test logging API errors."""
        endpoint = "/api/test"
        error_type = "validation_error"
        error_message = "Invalid input"
        user_id = "user123"

        with patch('services.monitoring.API_ERRORS') as mock_counter, \
             patch('services.monitoring.logger') as mock_logger:
            
            monitoring_svc.log_error(endpoint, error_type, error_message, user_id)

            # Verify Prometheus metrics
            mock_counter.labels.assert_called_with(endpoint=endpoint, error_type=error_type)
            mock_counter.labels.return_value.inc.assert_called_once()

            # Verify logging
            mock_logger.error.assert_called_once()

            # Verify Redis storage
            monitoring_svc.redis_client.client.lpush.assert_called_once()
            monitoring_svc.redis_client.client.expire.assert_called_once()

    def test_log_error_without_user_id(self, monitoring_svc):
        """Test logging error without user ID."""
        with patch('services.monitoring.API_ERRORS'), \
             patch('services.monitoring.logger'):
            
            monitoring_svc.log_error("/api/test", "error", "message")

            # Should work without user_id
            monitoring_svc.redis_client.client.lpush.assert_called_once()

    def test_track_token_usage(self, monitoring_svc):
        """Test tracking OpenAI token usage."""
        user_id = "user123"
        model = "gpt-4"
        tokens_used = 1000
        cost_usd = 0.02

        with patch('services.monitoring.TOKEN_USAGE') as mock_counter:
            monitoring_svc.track_token_usage(user_id, model, tokens_used, cost_usd)

            # Verify Prometheus metrics
            mock_counter.labels.assert_called_with(model=model, user_id=user_id)
            mock_counter.labels.return_value.inc.assert_called_with(tokens_used)

            # Verify Redis tracking
            monitoring_svc.redis_client.track_token_usage.assert_called_with(
                user_id, tokens_used, cost_usd, model
            )

    def test_get_metrics(self, monitoring_svc):
        """Test getting Prometheus metrics."""
        with patch('services.monitoring.generate_latest') as mock_generate:
            mock_generate.return_value = "prometheus_metrics_data"
            
            result = monitoring_svc.get_metrics()
            
            assert result == "prometheus_metrics_data"
            mock_generate.assert_called_once()

    def test_get_health_status_healthy(self, monitoring_svc):
        """Test getting health status when healthy."""
        # Mock Redis connection
        monitoring_svc.redis_client.is_connected.return_value = True
        monitoring_svc.redis_client.client.llen.return_value = 5

        health = monitoring_svc.get_health_status()

        assert health["status"] == "healthy"
        assert "uptime_seconds" in health
        assert "start_time" in health
        assert health["redis"] == "connected"
        assert health["error_count_today"] == 5
        assert health["version"] == "1.0.0"

    def test_get_health_status_redis_disconnected(self, monitoring_svc):
        """Test health status with Redis disconnected."""
        monitoring_svc.redis_client.is_connected.return_value = False

        health = monitoring_svc.get_health_status()

        assert health["redis"] == "disconnected"
        assert health["error_count_today"] == 0

    def test_get_analytics_redis_disconnected(self, monitoring_svc):
        """Test analytics when Redis is disconnected."""
        monitoring_svc.redis_client.is_connected.return_value = False

        result = monitoring_svc.get_analytics()

        assert result["error"] == "Redis not connected"

    def test_get_analytics_success(self, monitoring_svc):
        """Test successful analytics retrieval."""
        # Mock Redis data
        request_log_data = [
            json.dumps({
                "endpoint": "/api/test",
                "status": 200,
                "duration": 0.5
            }),
            json.dumps({
                "endpoint": "/api/test",
                "status": 404,
                "duration": 0.3
            }),
            json.dumps({
                "endpoint": "/api/other",
                "status": 200,
                "duration": 0.7
            })
        ]

        error_log_data = [
            json.dumps({
                "error_type": "validation_error"
            }),
            json.dumps({
                "error_type": "timeout_error"
            })
        ]

        monitoring_svc.redis_client.client.lrange.side_effect = [
            request_log_data,  # First call for request logs
            error_log_data,    # First call for error logs
            [],                # Subsequent calls return empty
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            []
        ]

        analytics = monitoring_svc.get_analytics(days=1)

        assert analytics["total_requests"] == 3
        assert analytics["popular_endpoints"]["/api/test"] == 2
        assert analytics["popular_endpoints"]["/api/other"] == 1
        assert analytics["request_counts"]["2xx"] == 2
        assert analytics["request_counts"]["4xx"] == 1
        assert analytics["error_counts"]["validation_error"] == 1
        assert analytics["error_counts"]["timeout_error"] == 1
        assert analytics["average_response_time"] == 0.5  # (0.5 + 0.3 + 0.7) / 3

    def test_get_analytics_invalid_json(self, monitoring_svc):
        """Test analytics with invalid JSON data."""
        # Mock Redis with invalid JSON
        monitoring_svc.redis_client.client.lrange.side_effect = [
            ["invalid_json", "also_invalid"],  # Request logs
            ["invalid_error_json"],            # Error logs
            [],  # Rest empty
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            []
        ]

        analytics = monitoring_svc.get_analytics(days=1)

        # Should handle invalid JSON gracefully
        assert analytics["total_requests"] == 0
        assert analytics["average_response_time"] == 0

    def test_cleanup_old_logs(self, monitoring_svc):
        """Test cleaning up old log entries."""
        monitoring_svc.cleanup_old_logs(days_to_keep=30)

        # Should delete old log keys
        assert monitoring_svc.redis_client.client.delete.call_count > 0

    def test_cleanup_old_logs_redis_disconnected(self, monitoring_svc):
        """Test cleanup when Redis is disconnected."""
        monitoring_svc.redis_client.is_connected.return_value = False

        # Should not raise an error
        monitoring_svc.cleanup_old_logs(days_to_keep=30)

        monitoring_svc.redis_client.client.delete.assert_not_called()


class TestGlobalMonitoringService:
    """Test global monitoring service functions."""

    def test_global_monitoring_service_exists(self):
        """Test that global monitoring_service exists."""
        assert monitoring_service is not None
        assert isinstance(monitoring_service, MonitoringService)

    def test_get_monitoring_service(self):
        """Test get_monitoring_service function."""
        service = get_monitoring_service()
        assert service is monitoring_service
        assert isinstance(service, MonitoringService)


class TestMonitoringServiceIntegration:
    """Integration tests for monitoring service."""

    def test_full_request_logging_flow(self):
        """Test complete request logging workflow."""
        with patch('services.monitoring.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.is_connected.return_value = True
            mock_get_redis.return_value = mock_redis

            service = MonitoringService()

            # Mock request/response
            mock_request = MagicMock(spec=Request)
            mock_request.method = "POST"
            mock_request.url.path = "/api/users"
            mock_request.headers.get.return_value = "Mozilla/5.0"
            mock_request.client.host = "192.168.1.1"

            mock_response = MagicMock(spec=Response)
            mock_response.status_code = 201

            with patch('services.monitoring.REQUEST_COUNT'), \
                 patch('services.monitoring.REQUEST_DURATION'):
                
                service.log_request(mock_request, mock_response, 0.8)

                # Verify Redis was called with correct data
                mock_redis.client.lpush.assert_called_once()
                call_args = mock_redis.client.lpush.call_args[0]
                
                assert "request_log:" in call_args[0]
                log_data = json.loads(call_args[1])
                assert log_data["method"] == "POST"
                assert log_data["endpoint"] == "/api/users"
                assert log_data["status"] == 201
                assert log_data["duration"] == 0.8

    def test_error_logging_and_analytics_flow(self):
        """Test error logging and analytics retrieval."""
        with patch('services.monitoring.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.is_connected.return_value = True
            mock_get_redis.return_value = mock_redis

            service = MonitoringService()

            # Log an error
            with patch('services.monitoring.API_ERRORS'), \
                 patch('services.monitoring.logger'):
                
                service.log_error("/api/test", "auth_error", "Unauthorized", "user123")

                # Verify error was logged to Redis
                mock_redis.client.lpush.assert_called()
                call_args = mock_redis.client.lpush.call_args[0]
                
                assert "error_log:" in call_args[0]
                error_data = json.loads(call_args[1])
                assert error_data["endpoint"] == "/api/test"
                assert error_data["error_type"] == "auth_error"
                assert error_data["user_id"] == "user123"