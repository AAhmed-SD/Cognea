import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

from services.performance import (
    PerformanceMonitor, performance_monitor, monitor_performance,
    DatabaseQueryOptimizer, ResponseTimeOptimizer, PerformanceMiddleware
)


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create a fresh PerformanceMonitor instance."""
        return PerformanceMonitor(max_history=100)

    def test_init(self, monitor):
        """Test PerformanceMonitor initialization."""
        assert monitor.max_history == 100
        assert len(monitor.response_times) == 0
        assert len(monitor.error_counts) == 0
        assert len(monitor.request_counts) == 0
        assert len(monitor.slow_queries) == 0
        assert isinstance(monitor.start_time, datetime)

    def test_record_request_success(self, monitor):
        """Test recording a successful request."""
        monitor.record_request("/api/test", "GET", 0.5, 200)
        
        key = "GET /api/test"
        assert monitor.request_counts[key] == 1
        assert monitor.error_counts[key] == 0
        assert len(monitor.response_times[key]) == 1
        assert monitor.response_times[key][0] == 0.5

    def test_record_request_error(self, monitor):
        """Test recording an error request."""
        monitor.record_request("/api/test", "POST", 0.3, 500)
        
        key = "POST /api/test"
        assert monitor.request_counts[key] == 1
        assert monitor.error_counts[key] == 1
        assert len(monitor.response_times[key]) == 1

    def test_record_slow_query(self, monitor):
        """Test recording a slow query."""
        monitor.record_request("/api/slow", "GET", 2.5, 200)
        
        assert len(monitor.slow_queries) == 1
        slow_query = monitor.slow_queries[0]
        assert slow_query["endpoint"] == "GET /api/slow"
        assert slow_query["response_time"] == 2.5
        assert slow_query["status_code"] == 200
        assert isinstance(slow_query["timestamp"], datetime)

    def test_slow_queries_limit(self, monitor):
        """Test slow queries list size limit."""
        # Add 105 slow queries
        for i in range(105):
            monitor.record_request(f"/api/slow{i}", "GET", 1.5, 200)
        
        # Should keep only last 100
        assert len(monitor.slow_queries) == 100

    def test_get_endpoint_stats_no_data(self, monitor):
        """Test getting stats for endpoint with no data."""
        stats = monitor.get_endpoint_stats("/api/test", "GET")
        
        assert stats["endpoint"] == "GET /api/test"
        assert stats["request_count"] == 0
        assert stats["error_count"] == 0
        assert stats["avg_response_time"] == 0
        assert stats["min_response_time"] == 0
        assert stats["max_response_time"] == 0

    def test_get_endpoint_stats_with_data(self, monitor):
        """Test getting stats for endpoint with data."""
        # Add some requests
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        for rt in response_times:
            monitor.record_request("/api/test", "GET", rt, 200)
        
        # Add one error
        monitor.record_request("/api/test", "GET", 0.6, 500)
        
        stats = monitor.get_endpoint_stats("/api/test", "GET")
        
        assert stats["endpoint"] == "GET /api/test"
        assert stats["request_count"] == 6
        assert stats["error_count"] == 1
        assert stats["avg_response_time"] == 0.35  # (0.1+0.2+0.3+0.4+0.5+0.6)/6
        assert stats["min_response_time"] == 0.1
        assert stats["max_response_time"] == 0.6

    def test_get_endpoint_stats_percentiles(self, monitor):
        """Test percentile calculations in endpoint stats."""
        # Add 100 requests with known response times
        for i in range(100):
            monitor.record_request("/api/test", "GET", i * 0.01, 200)
        
        stats = monitor.get_endpoint_stats("/api/test", "GET")
        
        # Should have percentile data
        assert "p95_response_time" in stats
        assert "p99_response_time" in stats
        assert stats["p95_response_time"] > 0
        assert stats["p99_response_time"] > 0

    def test_get_overall_stats_no_data(self, monitor):
        """Test getting overall stats with no data."""
        stats = monitor.get_overall_stats()
        
        assert stats["total_requests"] == 0
        assert stats["total_errors"] == 0
        assert stats["avg_response_time"] == 0
        assert stats["requests_per_second"] == 0

    def test_get_overall_stats_with_data(self, monitor):
        """Test getting overall stats with data."""
        # Add some requests
        monitor.record_request("/api/test1", "GET", 0.1, 200)
        monitor.record_request("/api/test2", "POST", 0.2, 201)
        monitor.record_request("/api/test3", "GET", 0.3, 500)
        
        stats = monitor.get_overall_stats()
        
        assert stats["total_requests"] == 3
        assert stats["total_errors"] == 1
        assert stats["avg_response_time"] == 0.2  # (0.1+0.2+0.3)/3
        assert stats["error_rate"] == 33.33333333333333  # 1/3 * 100
        assert stats["uptime_seconds"] > 0

    def test_get_slowest_endpoints(self, monitor):
        """Test getting slowest endpoints."""
        # Add requests with different response times
        monitor.record_request("/api/fast", "GET", 0.1, 200)
        monitor.record_request("/api/medium", "GET", 0.5, 200)
        monitor.record_request("/api/slow", "GET", 1.0, 200)
        
        slowest = monitor.get_slowest_endpoints(limit=2)
        
        assert len(slowest) == 2
        assert slowest[0]["endpoint"] == "GET /api/slow"
        assert slowest[1]["endpoint"] == "GET /api/medium"

    def test_get_recent_slow_queries(self, monitor):
        """Test getting recent slow queries."""
        # Add slow queries
        monitor.record_request("/api/slow1", "GET", 1.5, 200)
        monitor.record_request("/api/slow2", "POST", 2.0, 201)
        monitor.record_request("/api/slow3", "GET", 1.8, 500)
        
        recent = monitor.get_recent_slow_queries(limit=2)
        
        assert len(recent) == 2
        # Should return most recent first
        assert recent[0]["endpoint"] == "POST /api/slow2"
        assert recent[1]["endpoint"] == "GET /api/slow3"

    def test_clear_history(self, monitor):
        """Test clearing performance history."""
        # Add some data
        monitor.record_request("/api/test", "GET", 0.5, 200)
        monitor.record_request("/api/slow", "GET", 1.5, 200)
        
        # Clear history
        monitor.clear_history()
        
        assert len(monitor.response_times) == 0
        assert len(monitor.error_counts) == 0
        assert len(monitor.request_counts) == 0
        assert len(monitor.slow_queries) == 0


class TestGlobalPerformanceMonitor:
    """Test global performance monitor."""

    def test_global_monitor_exists(self):
        """Test that global performance_monitor exists."""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, PerformanceMonitor)


class TestMonitorPerformanceDecorator:
    """Test monitor_performance decorator."""

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test decorator with async function success."""
        @monitor_performance("/api/test")
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"
        
        initial_count = performance_monitor.request_counts.get("GET /api/test", 0)
        
        result = await test_func()
        
        assert result == "success"
        assert performance_monitor.request_counts["GET /api/test"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_async_function_error(self):
        """Test decorator with async function error."""
        @monitor_performance("/api/error")
        async def failing_func():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        initial_count = performance_monitor.request_counts.get("GET /api/error", 0)
        initial_errors = performance_monitor.error_counts.get("GET /api/error", 0)
        
        with pytest.raises(ValueError):
            await failing_func()
        
        assert performance_monitor.request_counts["GET /api/error"] == initial_count + 1
        assert performance_monitor.error_counts["GET /api/error"] == initial_errors + 1

    def test_sync_function_success(self):
        """Test decorator with sync function success."""
        @monitor_performance("/api/sync")
        def test_func():
            time.sleep(0.1)
            return "success"
        
        initial_count = performance_monitor.request_counts.get("GET /api/sync", 0)
        
        result = test_func()
        
        assert result == "success"
        assert performance_monitor.request_counts["GET /api/sync"] == initial_count + 1

    def test_sync_function_error(self):
        """Test decorator with sync function error."""
        @monitor_performance("/api/sync_error")
        def failing_func():
            time.sleep(0.1)
            raise ValueError("Test error")
        
        initial_count = performance_monitor.request_counts.get("GET /api/sync_error", 0)
        initial_errors = performance_monitor.error_counts.get("GET /api/sync_error", 0)
        
        with pytest.raises(ValueError):
            failing_func()
        
        assert performance_monitor.request_counts["GET /api/sync_error"] == initial_count + 1
        assert performance_monitor.error_counts["GET /api/sync_error"] == initial_errors + 1

    def test_decorator_without_endpoint(self):
        """Test decorator without explicit endpoint."""
        @monitor_performance()
        def test_func():
            return "success"
        
        initial_count = performance_monitor.request_counts.get("GET test_func", 0)
        
        result = test_func()
        
        assert result == "success"
        assert performance_monitor.request_counts["GET test_func"] == initial_count + 1


class TestDatabaseQueryOptimizer:
    """Test DatabaseQueryOptimizer class."""

    def test_optimize_select_query_basic(self):
        """Test basic SELECT query optimization."""
        query = DatabaseQueryOptimizer.optimize_select_query(
            "users", ["id", "name", "email"]
        )
        
        assert query == "SELECT id, name, email FROM users"

    def test_optimize_select_query_all_columns(self):
        """Test SELECT query with all columns."""
        query = DatabaseQueryOptimizer.optimize_select_query("users", [])
        
        assert query == "SELECT * FROM users"

    def test_optimize_select_query_with_filters(self):
        """Test SELECT query with filters."""
        filters = {"status": "active", "age": 25}
        query = DatabaseQueryOptimizer.optimize_select_query(
            "users", ["id", "name"], filters
        )
        
        assert "SELECT id, name FROM users" in query
        assert "WHERE" in query
        assert "status = %s" in query
        assert "age = %s" in query
        assert "AND" in query

    def test_optimize_select_query_with_in_filter(self):
        """Test SELECT query with IN filter."""
        filters = {"id": [1, 2, 3, 4, 5]}
        query = DatabaseQueryOptimizer.optimize_select_query(
            "users", ["name"], filters
        )
        
        assert "SELECT name FROM users" in query
        assert "WHERE id IN (%s, %s, %s, %s, %s)" in query

    def test_optimize_select_query_with_limit(self):
        """Test SELECT query with limit."""
        query = DatabaseQueryOptimizer.optimize_select_query(
            "users", ["id"], limit=10
        )
        
        assert query == "SELECT id FROM users LIMIT 10"

    def test_optimize_select_query_complete(self):
        """Test SELECT query with all options."""
        filters = {"status": "active", "role": ["admin", "user"]}
        query = DatabaseQueryOptimizer.optimize_select_query(
            "users", ["id", "name"], filters, limit=50
        )
        
        assert "SELECT id, name FROM users" in query
        assert "WHERE" in query
        assert "status = %s" in query
        assert "role IN (%s, %s)" in query
        assert "LIMIT 50" in query

    def test_should_use_index_equality(self):
        """Test index recommendation for equality operations."""
        assert DatabaseQueryOptimizer.should_use_index("user_id", "=", 123)
        assert DatabaseQueryOptimizer.should_use_index("status", "=", "active")

    def test_should_use_index_range(self):
        """Test index recommendation for range operations."""
        assert DatabaseQueryOptimizer.should_use_index("age", ">", 18)
        assert DatabaseQueryOptimizer.should_use_index("created_at", "<=", "2023-01-01")
        assert DatabaseQueryOptimizer.should_use_index("price", "BETWEEN", [10, 100])

    def test_should_use_index_in_clause(self):
        """Test index recommendation for IN clauses."""
        # Small IN clause should use index
        assert DatabaseQueryOptimizer.should_use_index("id", "IN", [1, 2, 3])
        
        # Large IN clause should use index (up to 100 items)
        large_list = list(range(100))
        assert DatabaseQueryOptimizer.should_use_index("id", "IN", large_list)
        
        # Very large IN clause should not use index
        very_large_list = list(range(101))
        assert not DatabaseQueryOptimizer.should_use_index("id", "IN", very_large_list)

    def test_should_not_use_index_like(self):
        """Test index recommendation for LIKE operations."""
        assert not DatabaseQueryOptimizer.should_use_index("name", "LIKE", "%test%")


class TestResponseTimeOptimizer:
    """Test ResponseTimeOptimizer class."""

    @pytest.mark.asyncio
    async def test_parallel_requests_success(self):
        """Test parallel execution of successful requests."""
        async def request1():
            await asyncio.sleep(0.1)
            return "result1"
        
        async def request2():
            await asyncio.sleep(0.1)
            return "result2"
        
        start_time = time.time()
        results = await asyncio.gather(request1(), request2(), return_exceptions=True)
        end_time = time.time()
        
        assert results == ["result1", "result2"]
        # Should complete in parallel (less than sequential time)
        assert end_time - start_time < 0.15

    @pytest.mark.asyncio
    async def test_parallel_requests_with_exception(self):
        """Test parallel execution with one request failing."""
        async def request1():
            await asyncio.sleep(0.1)
            return "result1"
        
        async def request2():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        results = await asyncio.gather(request1(), request2(), return_exceptions=True)
        
        assert results[0] == "result1"
        assert isinstance(results[1], ValueError)

    def test_batch_operations_even_split(self):
        """Test batch operations with even split."""
        items = list(range(10))
        batches = ResponseTimeOptimizer.batch_operations(items, batch_size=3)
        
        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_batch_operations_exact_split(self):
        """Test batch operations with exact split."""
        items = list(range(9))
        batches = ResponseTimeOptimizer.batch_operations(items, batch_size=3)
        
        assert len(batches) == 3
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]

    def test_batch_operations_empty_list(self):
        """Test batch operations with empty list."""
        batches = ResponseTimeOptimizer.batch_operations([], batch_size=5)
        
        assert batches == []

    def test_should_cache_response_get_success(self):
        """Test cache recommendation for successful GET requests."""
        assert ResponseTimeOptimizer.should_cache_response("/api/posts", "GET", 200)
        assert ResponseTimeOptimizer.should_cache_response("/api/categories", "GET", 200)

    def test_should_not_cache_response_user_data(self):
        """Test cache recommendation for user-specific data."""
        assert not ResponseTimeOptimizer.should_cache_response("/api/user/profile", "GET", 200)
        assert not ResponseTimeOptimizer.should_cache_response("/api/users/123", "GET", 200)

    def test_should_not_cache_response_non_get(self):
        """Test cache recommendation for non-GET requests."""
        assert not ResponseTimeOptimizer.should_cache_response("/api/posts", "POST", 201)
        assert not ResponseTimeOptimizer.should_cache_response("/api/posts", "PUT", 200)
        assert not ResponseTimeOptimizer.should_cache_response("/api/posts", "DELETE", 204)

    def test_should_not_cache_response_error(self):
        """Test cache recommendation for error responses."""
        assert not ResponseTimeOptimizer.should_cache_response("/api/posts", "GET", 404)
        assert not ResponseTimeOptimizer.should_cache_response("/api/posts", "GET", 500)


class TestPerformanceMiddleware:
    """Test PerformanceMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a mock ASGI app."""
        async def mock_app(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": []
            })
            await send({
                "type": "http.response.body",
                "body": b"OK"
            })
        return mock_app

    @pytest.fixture
    def middleware(self, app):
        """Create PerformanceMiddleware instance."""
        return PerformanceMiddleware(app)

    @pytest.mark.asyncio
    async def test_middleware_http_request(self, middleware):
        """Test middleware with HTTP request."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test"
        }
        
        received_messages = []
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        async def send(message):
            received_messages.append(message)
        
        initial_count = performance_monitor.request_counts.get("GET /api/test", 0)
        
        await middleware(scope, receive, send)
        
        # Should record the request
        assert performance_monitor.request_counts["GET /api/test"] == initial_count + 1
        
        # Should have sent response messages
        assert len(received_messages) == 2
        assert received_messages[0]["type"] == "http.response.start"
        assert received_messages[1]["type"] == "http.response.body"

    @pytest.mark.asyncio
    async def test_middleware_non_http_request(self, middleware):
        """Test middleware with non-HTTP request."""
        scope = {
            "type": "websocket",
            "path": "/ws"
        }
        
        received_messages = []
        
        async def receive():
            return {"type": "websocket.connect"}
        
        async def send(message):
            received_messages.append(message)
        
        # Should pass through without recording
        await middleware(scope, receive, send)
        
        # Should not record performance metrics for websocket
        assert "GET /ws" not in performance_monitor.request_counts