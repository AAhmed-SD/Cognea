import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring and optimization service"""

    def __init__(self, max_history: int = 1000):
        pass
        self.max_history = max_history
        self.response_times: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self.error_counts: dict[str, int] = defaultdict(int)
        self.request_counts: dict[str, int] = defaultdict(int)
        self.slow_queries: list[dict] = []
        self.start_time = datetime.utcnow()

    def record_request(
        self, endpoint: str, method: str, response_time: float, status_code: int = 200
    ):
        pass
        """Record a request for performance tracking"""
        key = f"{method} {endpoint}"
        self.response_times[key].append(response_time)
        self.request_counts[key] += 1

        if status_code >= 400:
            self.error_counts[key] += 1

        # Track slow requests (> 1 second)
        if response_time > 1.0:
            self.slow_queries.append(
                {
                    "endpoint": key,
                    "response_time": response_time,
                    "timestamp": datetime.utcnow(),
                    "status_code": status_code,
                }
            )

            # Keep only recent slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

    def get_endpoint_stats(self, endpoint: str, method: str = "GET") -> dict:
        """Get performance statistics for an endpoint"""
        key = f"{method} {endpoint}"
        times = list(self.response_times[key])

        if not times:
            return {
                "endpoint": key,
                "request_count": 0,
                "error_count": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
            }

        return {
            "endpoint": key,
            "request_count": self.request_counts[key],
            "error_count": self.error_counts[key],
            "avg_response_time": statistics.mean(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "p95_response_time": (
                statistics.quantiles(times, n=20)[18]
                if len(times) >= 20
                else max(times)
            ),
            "p99_response_time": (
                statistics.quantiles(times, n=100)[98]
                if len(times) >= 100
                else max(times)
            ),
        }

    def get_overall_stats(self) -> dict:
        """Get overall performance statistics"""
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)

        if not all_times:
            return {
                "total_requests": 0,
                "total_errors": 0,
                "avg_response_time": 0,
                "uptime_seconds": 0,
                "requests_per_second": 0,
            }

        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "avg_response_time": statistics.mean(all_times),
            "uptime_seconds": uptime,
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "error_rate": (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            ),
        }

    def get_slowest_endpoints(self, limit: int = 10) -> list[dict]:
        """Get the slowest endpoints"""
        endpoint_stats = []
        for key in self.response_times.keys():
            stats = self.get_endpoint_stats(key.split(" ", 1)[1], key.split(" ", 1)[0])
            if stats["request_count"] > 0:
                endpoint_stats.append(stats)

        return sorted(
            endpoint_stats, key=lambda x: x["avg_response_time"], reverse=True
        )[:limit]

    def get_recent_slow_queries(self, limit: int = 20) -> list[dict]:
        """Get recent slow queries"""
        return self.slow_queries[-limit:]

    def clear_history(self):
        """Clear performance history"""
        self.response_times.clear()
        self.error_counts.clear()
        self.request_counts.clear()
        self.slow_queries.clear()
        self.start_time = datetime.utcnow()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(endpoint: str = None):
    pass
    """Decorator to monitor endpoint performance"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                performance_monitor.record_request(
                    endpoint or func.__name__, "GET", response_time, 200
                )
                return result
            except Exception:
                response_time = time.time() - start_time
                performance_monitor.record_request(
                    endpoint or func.__name__, "GET", response_time, 500
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                performance_monitor.record_request(
                    endpoint or func.__name__, "GET", response_time, 200
                )
                return result
            except Exception:
                response_time = time.time() - start_time
                performance_monitor.record_request(
                    endpoint or func.__name__, "GET", response_time, 500
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class DatabaseQueryOptimizer:
    """Database query optimization utilities"""

    @staticmethod
    def optimize_select_query(
        table: str, columns: list[str], filters: dict = None, limit: int = None
    ) -> str:
        """Generate optimized SELECT query"""
        # Only select needed columns
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table}"

        # Add filters
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    placeholders = ", ".join(["%s"] * len(value))
                    conditions.append(f"{key} IN ({placeholders})")
                else:
                    conditions.append(f"{key} = %s")
            query += f" WHERE {' AND '.join(conditions)}"

        # Add limit
        if limit:
            query += f" LIMIT {limit}"

        return query

    @staticmethod
    def should_use_index(column: str, operation: str, value: Any) -> bool:
        """Determine if an index should be used for a query"""
        # Use index for equality comparisons and range queries
        if operation in ["=", ">", "<", ">=", "<=", "BETWEEN"]:
            return True

        # Use index for IN clauses with reasonable number of values
        if operation == "IN" and isinstance(value, (list, tuple)) and len(value) <= 100:
            return True

        return False


class ResponseTimeOptimizer:
    """Response time optimization utilities"""

    @staticmethod
    async def parallel_requests(requests: list[Callable]) -> list[Any]:
        """Execute multiple requests in parallel"""
        return await asyncio.gather(*requests, return_exceptions=True)

    @staticmethod
    def batch_operations(items: list[Any], batch_size: int = 100) -> list[list[Any]]:
        """Split items into batches for batch processing"""
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    @staticmethod
    def should_cache_response(endpoint: str, method: str, status_code: int) -> bool:
        """Determine if a response should be cached"""
        # Cache successful GET requests
        if method == "GET" and status_code == 200:
            # Don't cache user-specific data
            if "user" in endpoint.lower() or "profile" in endpoint.lower():
                return False
            return True

        return False


# Performance middleware for FastAPI
class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()

            # Create a custom send function to capture response time
            async def custom_send(message):
                if message["type"] == "http.response.start":
                    response_time = time.time() - start_time
                    method = scope.get("method", "GET")
                    path = scope.get("path", "/")
                    status = message.get("status", 200)

                    performance_monitor.record_request(
                        path, method, response_time, status
                    )

                await send(message)

            await self.app(scope, receive, custom_send)
        else:
            await self.app(scope, receive, send)
