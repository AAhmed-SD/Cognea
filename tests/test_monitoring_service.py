import pytest
import json
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch, Mock
from fastapi import Request, Response

from services.monitoring import (
    MonitoringService,
    monitoring_service,
    get_monitoring_service,
    REQUEST_COUNT,
    REQUEST_DURATION,
    ACTIVE_USERS,
    TOKEN_USAGE,
    API_ERRORS
)


class TestMonitoringService:
    """Test MonitoringService functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.client = MagicMock()
        return mock_client

    @pytest.fixture
    def mock_redis_disconnected(self):
        """Mock disconnected Redis client for testing."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = False
        return mock_client

    @pytest.fixture
    def monitoring_service_instance(self, mock_redis_client):
        """Create a MonitoringService instance for testing."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            service = MonitoringService()
            return service

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request object."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = {"user-agent": "test-agent"}
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock FastAPI Response object."""
        response = MagicMock(spec=Response)
        response.status_code = 200
        return response

    def test_monitoring_service_initialization(self, monitoring_service_instance):
        """Test MonitoringService initialization."""
        assert monitoring_service_instance is not None
        assert hasattr(monitoring_service_instance, 'redis_client')
        assert hasattr(monitoring_service_instance, 'start_time')
        assert isinstance(monitoring_service_instance.start_time, datetime)

    def test_log_request_success(self, monitoring_service_instance, mock_request, mock_response):
        """Test successful request logging."""
        duration = 0.123
        
        monitoring_service_instance.log_request(mock_request, mock_response, duration)
        
        # Verify Redis operations
        monitoring_service_instance.redis_client.client.lpush.assert_called_once()
        monitoring_service_instance.redis_client.client.expire.assert_called_once()
        
        # Check the logged data structure
        call_args = monitoring_service_instance.redis_client.client.lpush.call_args
        log_data = json.loads(call_args[0][1])
        
        assert "timestamp" in log_data
        assert log_data["method"] == "GET"
        assert log_data["endpoint"] == "/api/test"
        assert log_data["status"] == 200
        assert log_data["duration"] == duration
        assert log_data["user_agent"] == "test-agent"
        assert log_data["ip"] == "127.0.0.1"

    def test_log_request_redis_disconnected(self, mock_redis_disconnected, mock_request, mock_response):
        """Test request logging when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            # Should not raise exception
            service.log_request(mock_request, mock_response, 0.123)
            
            # Redis operations should not be called
            mock_redis_disconnected.client.lpush.assert_not_called()

    def test_log_request_different_methods(self, monitoring_service_instance, mock_response):
        """Test logging requests with different HTTP methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        for method in methods:
            mock_request = MagicMock(spec=Request)
            mock_request.method = method
            mock_request.url.path = f"/api/{method.lower()}"
            mock_request.headers = {"user-agent": "test-agent"}
            mock_request.client.host = "127.0.0.1"
            
            monitoring_service_instance.log_request(mock_request, mock_response, 0.1)
            
            # Verify the method is logged correctly
            call_args = monitoring_service_instance.redis_client.client.lpush.call_args
            log_data = json.loads(call_args[0][1])
            assert log_data["method"] == method

    def test_log_request_different_status_codes(self, monitoring_service_instance, mock_request):
        """Test logging requests with different status codes."""
        status_codes = [200, 201, 400, 401, 404, 500]
        
        for status_code in status_codes:
            mock_response = MagicMock(spec=Response)
            mock_response.status_code = status_code
            
            monitoring_service_instance.log_request(mock_request, mock_response, 0.1)
            
            # Verify the status code is logged correctly
            call_args = monitoring_service_instance.redis_client.client.lpush.call_args
            log_data = json.loads(call_args[0][1])
            assert log_data["status"] == status_code

    def test_log_error_success(self, monitoring_service_instance):
        """Test successful error logging."""
        endpoint = "/api/test"
        error_type = "ValidationError"
        error_message = "Invalid input data"
        user_id = "user123"
        
        monitoring_service_instance.log_error(endpoint, error_type, error_message, user_id)
        
        # Verify Redis operations
        monitoring_service_instance.redis_client.client.lpush.assert_called_once()
        monitoring_service_instance.redis_client.client.expire.assert_called_once()
        
        # Check the logged error data
        call_args = monitoring_service_instance.redis_client.client.lpush.call_args
        error_data = json.loads(call_args[0][1])
        
        assert "timestamp" in error_data
        assert error_data["endpoint"] == endpoint
        assert error_data["error_type"] == error_type
        assert error_data["error_message"] == error_message
        assert error_data["user_id"] == user_id

    def test_log_error_without_user_id(self, monitoring_service_instance):
        """Test error logging without user ID."""
        endpoint = "/api/test"
        error_type = "ServerError"
        error_message = "Internal server error"
        
        monitoring_service_instance.log_error(endpoint, error_type, error_message)
        
        # Check the logged error data
        call_args = monitoring_service_instance.redis_client.client.lpush.call_args
        error_data = json.loads(call_args[0][1])
        
        assert error_data["user_id"] is None

    def test_log_error_redis_disconnected(self, mock_redis_disconnected):
        """Test error logging when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            # Should not raise exception
            service.log_error("/api/test", "Error", "Test error")
            
            # Redis operations should not be called
            mock_redis_disconnected.client.lpush.assert_not_called()

    def test_track_token_usage_success(self, monitoring_service_instance):
        """Test successful token usage tracking."""
        user_id = "user123"
        model = "gpt-3.5-turbo"
        tokens_used = 150
        cost_usd = 0.03
        
        monitoring_service_instance.track_token_usage(user_id, model, tokens_used, cost_usd)
        
        # Verify Redis operations
        monitoring_service_instance.redis_client.track_token_usage.assert_called_once_with(
            user_id, tokens_used, cost_usd, model
        )

    def test_track_token_usage_redis_disconnected(self, mock_redis_disconnected):
        """Test token usage tracking when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            # Should not raise exception
            service.track_token_usage("user123", "gpt-4", 100, 0.02)
            
            # Redis operations should not be called
            mock_redis_disconnected.track_token_usage.assert_not_called()

    def test_get_metrics(self, monitoring_service_instance):
        """Test getting Prometheus metrics."""
        with patch('services.monitoring.generate_latest') as mock_generate:
            mock_generate.return_value = "prometheus_metrics_data"
            
            result = monitoring_service_instance.get_metrics()
            
            assert result == "prometheus_metrics_data"
            mock_generate.assert_called_once()

    def test_get_health_status_redis_connected(self, monitoring_service_instance):
        """Test health status when Redis is connected."""
        monitoring_service_instance.redis_client.client.llen.return_value = 5
        
        health = monitoring_service_instance.get_health_status()
        
        assert health["status"] == "healthy"
        assert "uptime_seconds" in health
        assert "start_time" in health
        assert health["redis"] == "connected"
        assert health["error_count_today"] == 5
        assert health["version"] == "1.0.0"

    def test_get_health_status_redis_disconnected(self, mock_redis_disconnected):
        """Test health status when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            health = service.get_health_status()
            
            assert health["status"] == "healthy"
            assert health["redis"] == "disconnected"
            assert health["error_count_today"] == 0

    def test_get_analytics_redis_disconnected(self, mock_redis_disconnected):
        """Test analytics when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            analytics = service.get_analytics()
            
            assert analytics == {"error": "Redis not connected"}

    def test_get_analytics_success(self, monitoring_service_instance):
        """Test successful analytics retrieval."""
        # Mock Redis data
        mock_request_logs = [
            json.dumps({
                "endpoint": "/api/users",
                "status": 200,
                "duration": 0.1
            }),
            json.dumps({
                "endpoint": "/api/tasks",
                "status": 201,
                "duration": 0.2
            }),
            json.dumps({
                "endpoint": "/api/users",
                "status": 404,
                "duration": 0.05
            })
        ]
        
        mock_error_logs = [
            json.dumps({
                "error_type": "ValidationError"
            }),
            json.dumps({
                "error_type": "AuthenticationError"
            })
        ]
        
        monitoring_service_instance.redis_client.client.lrange.side_effect = [
            mock_request_logs,  # Request logs for day 0
            mock_error_logs,    # Error logs for day 0
            [],  # Request logs for day 1
            [],  # Error logs for day 1
            # ... and so on for remaining days
        ] + [[], []] * 6  # Empty logs for remaining days
        
        analytics = monitoring_service_instance.get_analytics(days=7)
        
        assert "request_counts" in analytics
        assert "error_counts" in analytics
        assert "popular_endpoints" in analytics
        assert analytics["total_requests"] == 3
        assert analytics["popular_endpoints"]["/api/users"] == 2
        assert analytics["popular_endpoints"]["/api/tasks"] == 1
        assert analytics["request_counts"]["2xx"] == 2
        assert analytics["request_counts"]["4xx"] == 1
        assert analytics["error_counts"]["ValidationError"] == 1
        assert analytics["error_counts"]["AuthenticationError"] == 1

    def test_get_analytics_malformed_json(self, monitoring_service_instance):
        """Test analytics with malformed JSON logs."""
        # Mock Redis data with invalid JSON
        mock_request_logs = [
            "invalid json",
            json.dumps({
                "endpoint": "/api/users",
                "status": 200,
                "duration": 0.1
            })
        ]
        
        monitoring_service_instance.redis_client.client.lrange.side_effect = [
            mock_request_logs,
            [],  # Error logs
        ] + [[], []] * 6  # Empty logs for remaining days
        
        analytics = monitoring_service_instance.get_analytics(days=1)
        
        # Should handle malformed JSON gracefully
        assert analytics["total_requests"] == 1
        assert analytics["popular_endpoints"]["/api/users"] == 1

    def test_cleanup_old_logs_success(self, monitoring_service_instance):
        """Test successful cleanup of old logs."""
        monitoring_service_instance.cleanup_old_logs(days_to_keep=30)
        
        # Should call delete for old log keys
        assert monitoring_service_instance.redis_client.client.delete.call_count > 0

    def test_cleanup_old_logs_redis_disconnected(self, mock_redis_disconnected):
        """Test cleanup when Redis is disconnected."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_disconnected):
            service = MonitoringService()
            
            # Should not raise exception
            service.cleanup_old_logs(days_to_keep=30)
            
            # Delete should not be called
            mock_redis_disconnected.client.delete.assert_not_called()

    def test_cleanup_old_logs_custom_retention(self, monitoring_service_instance):
        """Test cleanup with custom retention period."""
        monitoring_service_instance.cleanup_old_logs(days_to_keep=7)
        
        # Should call delete for appropriate number of days
        assert monitoring_service_instance.redis_client.client.delete.call_count > 0


class TestMonitoringServiceIntegration:
    """Integration tests for MonitoringService."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for integration tests."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.client = MagicMock()
        return mock_client

    def test_global_monitoring_service_instance(self):
        """Test that global monitoring_service instance exists."""
        assert monitoring_service is not None
        assert isinstance(monitoring_service, MonitoringService)

    def test_get_monitoring_service_function(self):
        """Test get_monitoring_service function."""
        service = get_monitoring_service()
        assert service is not None
        assert isinstance(service, MonitoringService)
        assert service is monitoring_service

    def test_prometheus_metrics_exist(self):
        """Test that Prometheus metrics are defined."""
        assert REQUEST_COUNT is not None
        assert REQUEST_DURATION is not None
        assert ACTIVE_USERS is not None
        assert TOKEN_USAGE is not None
        assert API_ERRORS is not None

    def test_full_request_logging_workflow(self, mock_redis_client):
        """Test complete request logging workflow."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            service = MonitoringService()
            
            # Create mock request and response
            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = "/api/tasks"
            request.headers = {"user-agent": "test-browser"}
            request.client.host = "192.168.1.100"
            
            response = MagicMock(spec=Response)
            response.status_code = 201
            
            # Log request
            service.log_request(request, response, 0.234)
            
            # Verify Redis operations
            mock_redis_client.client.lpush.assert_called_once()
            mock_redis_client.client.expire.assert_called_once()
            
            # Verify log structure
            call_args = mock_redis_client.client.lpush.call_args
            key = call_args[0][0]
            log_data = json.loads(call_args[0][1])
            
            assert key.startswith("request_log:")
            assert log_data["method"] == "POST"
            assert log_data["endpoint"] == "/api/tasks"
            assert log_data["status"] == 201

    def test_full_error_logging_workflow(self, mock_redis_client):
        """Test complete error logging workflow."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            service = MonitoringService()
            
            # Log error
            service.log_error(
                endpoint="/api/auth/login",
                error_type="AuthenticationError",
                error_message="Invalid credentials",
                user_id="user456"
            )
            
            # Verify Redis operations
            mock_redis_client.client.lpush.assert_called_once()
            mock_redis_client.client.expire.assert_called_once()
            
            # Verify error log structure
            call_args = mock_redis_client.client.lpush.call_args
            key = call_args[0][0]
            error_data = json.loads(call_args[0][1])
            
            assert key.startswith("error_log:")
            assert error_data["endpoint"] == "/api/auth/login"
            assert error_data["error_type"] == "AuthenticationError"
            assert error_data["user_id"] == "user456"

    def test_analytics_calculation_accuracy(self, mock_redis_client):
        """Test analytics calculation accuracy."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            service = MonitoringService()
            
            # Mock comprehensive analytics data
            request_logs = [
                json.dumps({"endpoint": "/api/users", "status": 200, "duration": 0.1}),
                json.dumps({"endpoint": "/api/users", "status": 200, "duration": 0.2}),
                json.dumps({"endpoint": "/api/tasks", "status": 201, "duration": 0.15}),
                json.dumps({"endpoint": "/api/auth", "status": 401, "duration": 0.05}),
                json.dumps({"endpoint": "/api/tasks", "status": 500, "duration": 0.3}),
            ]
            
            error_logs = [
                json.dumps({"error_type": "ValidationError"}),
                json.dumps({"error_type": "ValidationError"}),
                json.dumps({"error_type": "ServerError"}),
            ]
            
            # Mock Redis responses for 1 day
            mock_redis_client.client.lrange.side_effect = [request_logs, error_logs]
            
            analytics = service.get_analytics(days=1)
            
            # Verify calculations
            assert analytics["total_requests"] == 5
            assert analytics["average_response_time"] == 0.16  # (0.1+0.2+0.15+0.05+0.3)/5
            assert analytics["popular_endpoints"]["/api/users"] == 2
            assert analytics["popular_endpoints"]["/api/tasks"] == 2
            assert analytics["popular_endpoints"]["/api/auth"] == 1
            assert analytics["request_counts"]["2xx"] == 3
            assert analytics["request_counts"]["4xx"] == 1
            assert analytics["request_counts"]["5xx"] == 1
            assert analytics["error_counts"]["ValidationError"] == 2
            assert analytics["error_counts"]["ServerError"] == 1


class TestMonitoringServiceEdgeCases:
    """Test edge cases for MonitoringService."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for edge case tests."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.client = MagicMock()
        return mock_client

    @pytest.fixture
    def monitoring_service_instance(self, mock_redis_client):
        """Create a MonitoringService instance for edge case testing."""
        with patch('services.monitoring.get_redis_client', return_value=mock_redis_client):
            service = MonitoringService()
            return service

    def test_request_logging_missing_headers(self, monitoring_service_instance):
        """Test request logging with missing headers."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = {}  # Empty headers
        request.client.host = "127.0.0.1"
        
        response = MagicMock(spec=Response)
        response.status_code = 200
        
        # Should not raise exception
        monitoring_service_instance.log_request(request, response, 0.1)
        
        # Verify user-agent defaults to empty string
        call_args = monitoring_service_instance.redis_client.client.lpush.call_args
        log_data = json.loads(call_args[0][1])
        assert log_data["user_agent"] == ""

    def test_analytics_empty_logs(self, monitoring_service_instance):
        """Test analytics with empty logs."""
        # Mock empty Redis responses
        monitoring_service_instance.redis_client.client.lrange.return_value = []
        
        analytics = monitoring_service_instance.get_analytics(days=1)
        
        assert analytics["total_requests"] == 0
        assert analytics["average_response_time"] == 0
        assert analytics["popular_endpoints"] == {}
        assert analytics["request_counts"] == {}
        assert analytics["error_counts"] == {}

    def test_health_status_uptime_calculation(self, monitoring_service_instance):
        """Test health status uptime calculation."""
        # Mock start time to be 1 hour ago
        monitoring_service_instance.start_time = datetime.now(UTC) - timedelta(hours=1)
        monitoring_service_instance.redis_client.client.llen.return_value = 0
        
        health = monitoring_service_instance.get_health_status()
        
        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= health["uptime_seconds"] <= 3610

    def test_large_analytics_dataset(self, monitoring_service_instance):
        """Test analytics with large dataset."""
        # Create large dataset
        large_request_logs = []
        for i in range(1000):
            large_request_logs.append(json.dumps({
                "endpoint": f"/api/endpoint{i % 10}",
                "status": 200 if i % 5 != 0 else 404,
                "duration": 0.1 + (i % 100) / 1000
            }))
        
        monitoring_service_instance.redis_client.client.lrange.side_effect = [
            large_request_logs, []  # Request logs, empty error logs
        ]
        
        analytics = monitoring_service_instance.get_analytics(days=1)
        
        assert analytics["total_requests"] == 1000
        assert len(analytics["popular_endpoints"]) == 10
        # 800 successful (200) + 200 not found (404)
        assert analytics["request_counts"]["2xx"] == 800
        assert analytics["request_counts"]["4xx"] == 200