"""
Monitoring and logging service for production deployment.
"""

import logging
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from services.redis_client import get_redis_client

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration")
ACTIVE_USERS = Gauge("active_users_total", "Total active users")
TOKEN_USAGE = Counter(
    "openai_tokens_total", "Total OpenAI tokens used", ["model", "user_id"]
)
API_ERRORS = Counter("api_errors_total", "Total API errors", ["endpoint", "error_type"])

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring application performance and usage."""

    def __init__(self):
        self.redis_client = get_redis_client()
        self.start_time = datetime.now(UTC)

    def log_request(self, request: Request, response: Response, duration: float):
        """Log HTTP request metrics."""
        method = request.method
        endpoint = request.url.path
        status = response.status_code

        # Increment Prometheus metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.observe(duration)

        # Log to Redis for analytics
        if self.redis_client.is_connected():
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "duration": duration,
                "user_agent": request.headers.get("user-agent", ""),
                "ip": request.client.host,
            }

            # Store in Redis with 24-hour expiration
            key = f"request_log:{datetime.now(UTC).strftime('%Y-%m-%d')}"
            self.redis_client.client.lpush(key, json.dumps(log_entry))
            self.redis_client.client.expire(key, 24 * 3600)  # 24 hours

    def log_error(
        self,
        endpoint: str,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
    ):
        """Log API errors."""
        API_ERRORS.labels(endpoint=endpoint, error_type=error_type).inc()

        error_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "endpoint": endpoint,
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id,
        }

        logger.error(f"API Error: {json.dumps(error_entry)}")

        # Store in Redis
        if self.redis_client.is_connected():
            key = f"error_log:{datetime.now(UTC).strftime('%Y-%m-%d')}"
            self.redis_client.client.lpush(key, json.dumps(error_entry))
            self.redis_client.client.expire(key, 7 * 24 * 3600)  # 7 days

    def track_token_usage(
        self, user_id: str, model: str, tokens_used: int, cost_usd: float
    ):
        """Track OpenAI token usage."""
        TOKEN_USAGE.labels(model=model, user_id=user_id).inc(tokens_used)

        # Store in Redis for analytics
        if self.redis_client.is_connected():
            self.redis_client.track_token_usage(user_id, tokens_used, cost_usd, model)

    def get_metrics(self) -> str:
        """Get Prometheus metrics."""
        return generate_latest()

    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        uptime = datetime.now(UTC) - self.start_time

        # Get Redis status
        redis_status = (
            "connected" if self.redis_client.is_connected() else "disconnected"
        )

        # Get recent error count
        error_count = 0
        if self.redis_client.is_connected():
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            error_key = f"error_log:{today}"
            error_count = self.redis_client.client.llen(error_key)

        return {
            "status": "healthy",
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "redis": redis_status,
            "error_count_today": error_count,
            "version": "1.0.0",
        }

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics data."""
        if not self.redis_client.is_connected():
            return {"error": "Redis not connected"}

        analytics = {
            "request_counts": {},
            "error_counts": {},
            "popular_endpoints": {},
            "average_response_time": 0,
            "total_requests": 0,
        }

        total_duration = 0
        total_requests = 0

        # Collect data from last N days
        for i in range(days):
            date = (datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d")

            # Request logs
            request_key = f"request_log:{date}"
            request_logs = self.redis_client.client.lrange(request_key, 0, -1)

            for log_str in request_logs:
                try:
                    log = json.loads(log_str)
                    endpoint = log.get("endpoint", "unknown")
                    status = log.get("status", 0)
                    duration = log.get("duration", 0)

                    # Count requests by endpoint
                    if endpoint not in analytics["popular_endpoints"]:
                        analytics["popular_endpoints"][endpoint] = 0
                    analytics["popular_endpoints"][endpoint] += 1

                    # Count by status
                    status_key = f"{status//100}xx"
                    if status_key not in analytics["request_counts"]:
                        analytics["request_counts"][status_key] = 0
                    analytics["request_counts"][status_key] += 1

                    total_duration += duration
                    total_requests += 1

                except json.JSONDecodeError:
                    continue

            # Error logs
            error_key = f"error_log:{date}"
            error_logs = self.redis_client.client.lrange(error_key, 0, -1)

            for log_str in error_logs:
                try:
                    log = json.loads(log_str)
                    error_type = log.get("error_type", "unknown")

                    if error_type not in analytics["error_counts"]:
                        analytics["error_counts"][error_type] = 0
                    analytics["error_counts"][error_type] += 1

                except json.JSONDecodeError:
                    continue

        # Calculate averages
        if total_requests > 0:
            analytics["average_response_time"] = total_duration / total_requests
        analytics["total_requests"] = total_requests

        return analytics

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log entries."""
        if not self.redis_client.is_connected():
            return

        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        # Clean up request logs
        for i in range(days_to_keep + 1, days_to_keep + 31):  # Clean up extra days
            date = (datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d")
            request_key = f"request_log:{date}"
            error_key = f"error_log:{date}"

            self.redis_client.client.delete(request_key)
            self.redis_client.client.delete(error_key)


# Global monitoring service instance
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    return monitoring_service
