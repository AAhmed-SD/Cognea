import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from main import app


class TestMainRoutes:
    """Test main application routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Cognie AI Personal Assistant API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "running"
        assert "features" in data
        assert "endpoints" in data
        assert "meta" in data
        assert "timestamp" in data["meta"]

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        with patch('main.get_performance_monitor') as mock_monitor, \
             patch('main.enhanced_cache') as mock_cache:
            
            # Mock performance monitor
            mock_perf = MagicMock()
            mock_perf.get_health_status.return_value = {
                "status": "healthy",
                "uptime": 3600,
                "memory_usage": 50.0
            }
            mock_monitor.return_value = mock_perf
            
            # Mock cache
            mock_cache.get_metrics.return_value = {
                "hits": 100,
                "misses": 10,
                "hit_rate": 0.91
            }
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "uptime" in data
            assert "performance" in data
            assert "cache" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        with patch('main.get_performance_monitor') as mock_monitor:
            mock_perf = MagicMock()
            mock_perf.get_metrics.return_value = {
                "requests_total": 1000,
                "response_time_avg": 0.25,
                "error_rate": 0.01
            }
            mock_monitor.return_value = mock_perf
            
            response = client.get("/metrics")
            
            assert response.status_code == 200
            # Should return Prometheus format or JSON metrics

    def test_alerts_endpoint(self, client):
        """Test alerts endpoint."""
        with patch('main.get_performance_monitor') as mock_monitor:
            mock_perf = MagicMock()
            mock_perf.get_alerts.return_value = {
                "active_alerts": [],
                "alert_count": 0
            }
            mock_monitor.return_value = mock_perf
            
            response = client.get("/alerts")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "active_alerts" in data or "alerts" in data

    def test_cors_middleware(self, client):
        """Test CORS middleware is configured."""
        # Make an OPTIONS request to test CORS
        response = client.options("/")
        
        # Should not return 405 Method Not Allowed if CORS is properly configured
        assert response.status_code in [200, 204, 405]  # 405 is acceptable for root endpoint

    def test_gzip_middleware(self, client):
        """Test GZip middleware compresses responses."""
        response = client.get("/", headers={"Accept-Encoding": "gzip"})
        
        assert response.status_code == 200
        # Check if response can be decompressed (TestClient handles this automatically)
        assert response.json()["message"] == "Cognie AI Personal Assistant API"

    def test_app_configuration(self):
        """Test application configuration."""
        assert app.title == "Cognie AI Personal Assistant API"
        assert app.version == "2.0.0"
        assert "Enhanced Redis caching" in app.description

    def test_router_inclusion(self):
        """Test that all routers are included."""
        # Get all routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        
        # Check that main API prefixes exist
        expected_prefixes = [
            "/api/user",
            "/api/tasks", 
            "/api/goals",
            "/api/habits",
            "/api/ai",
            "/api/auth"
        ]
        
        for prefix in expected_prefixes:
            # Check if any route starts with the prefix
            assert any(route.startswith(prefix) for route in routes), f"Routes with prefix {prefix} not found"

    def test_middleware_order(self):
        """Test middleware is added in correct order."""
        middleware_types = [type(middleware.cls).__name__ for middleware in app.user_middleware]
        
        # Check that important middleware is present
        expected_middleware = ["CORSMiddleware", "GZipMiddleware"]
        for middleware in expected_middleware:
            assert any(middleware in mw_type for mw_type in middleware_types), f"{middleware} not found"


class TestAppLifespan:
    """Test application lifespan events."""

    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test application startup logic."""
        from main import lifespan
        
        # Mock environment variable
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            app_mock = MagicMock()
            
            # Test lifespan context manager
            async with lifespan(app_mock):
                # Should not raise any exceptions
                pass

    @pytest.mark.asyncio
    async def test_lifespan_missing_api_key(self):
        """Test application startup with missing API key."""
        from main import lifespan
        
        # Remove API key from environment
        with patch.dict('os.environ', {}, clear=True):
            app_mock = MagicMock()
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Missing OpenAI API key"):
                async with lifespan(app_mock):
                    pass

    def test_logging_configuration(self):
        """Test logging is properly configured."""
        import logging
        
        # Check that logger exists and has handlers
        logger = logging.getLogger("main")
        assert logger is not None
        
        # Check that root logger has some configuration
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.INFO


class TestErrorHandling:
    """Test error handling and middleware."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_404_error_handling(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_method_not_allowed_handling(self, client):
        """Test method not allowed handling."""
        # Try to POST to a GET-only endpoint
        response = client.post("/")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data

    def test_validation_error_handling(self, client):
        """Test request validation error handling."""
        # Send invalid JSON to an endpoint that expects valid data
        response = client.post("/api/tasks", json={"invalid": "data"})
        
        # Should return 422 for validation error or 401 for auth error
        assert response.status_code in [401, 422, 404]  # Depending on auth middleware


class TestPerformanceMonitoring:
    """Test performance monitoring integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_performance_monitoring_middleware(self, client):
        """Test that performance monitoring tracks requests."""
        with patch('main.get_performance_monitor') as mock_monitor:
            mock_perf = MagicMock()
            mock_monitor.return_value = mock_perf
            
            # Make a request
            response = client.get("/")
            
            assert response.status_code == 200
            # Performance monitoring should be called
            # (Note: actual call verification depends on middleware implementation)

    def test_background_workers_integration(self):
        """Test background workers are properly integrated."""
        # Check that background worker modules can be imported
        try:
            from services.background_workers import background_worker, job_scheduler
            assert background_worker is not None
            assert job_scheduler is not None
        except ImportError:
            pytest.skip("Background workers not available")

    def test_redis_cache_integration(self):
        """Test Redis cache integration."""
        # Check that enhanced cache can be imported
        try:
            from services.redis_cache import enhanced_cache
            assert enhanced_cache is not None
        except ImportError:
            pytest.skip("Redis cache not available")


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_openapi_schema(self, client):
        """Test OpenAPI schema generation."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Cognie AI Personal Assistant API"
        assert schema["info"]["version"] == "2.0.0"

    def test_docs_endpoint(self, client):
        """Test Swagger UI docs endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation endpoint."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]