"""
Prometheus integration for metrics collection and monitoring.
"""

import logging
import time

from fastapi import FastAPI, Request
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from config.monitoring import monitoring_config

logger = logging.getLogger(__name__)


class PrometheusService:
    """Service for Prometheus metrics collection and monitoring."""

    def __init__(self):
        self.initialized = False

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status", "user_id"]
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "status"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )

        # AI Service Metrics
        self.ai_requests_total = Counter(
            "ai_requests_total",
            "Total AI service requests",
            ["provider", "task_type", "status", "user_id"]
        )

        self.ai_request_duration_seconds = Histogram(
            "ai_request_duration_seconds",
            "AI request duration in seconds",
            ["provider", "task_type"],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
        )

        self.ai_tokens_used_total = Counter(
            "ai_tokens_used_total",
            "Total AI tokens used",
            ["provider", "task_type", "token_type", "user_id"]
        )

        self.ai_cost_total = Counter(
            "ai_cost_total",
            "Total AI cost in USD",
            ["provider", "task_type", "user_id"]
        )

        # Database Metrics
        self.db_operations_total = Counter(
            "db_operations_total",
            "Total database operations",
            ["operation", "table", "status"]
        )

        self.db_operation_duration_seconds = Histogram(
            "db_operation_duration_seconds",
            "Database operation duration in seconds",
            ["operation", "table"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
        )

        # Cache Metrics
        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "status"]
        )

        self.cache_hit_ratio = Gauge(
            "cache_hit_ratio",
            "Cache hit ratio",
            ["cache_type"]
        )

        # User Metrics
        self.active_users = Gauge(
            "active_users_total",
            "Total active users"
        )

        self.user_sessions_total = Counter(
            "user_sessions_total",
            "Total user sessions",
            ["status"]
        )

        # Business Metrics
        self.subscriptions_total = Counter(
            "subscriptions_total",
            "Total subscriptions",
            ["plan", "status"]
        )

        self.revenue_total = Counter(
            "revenue_total",
            "Total revenue in USD",
            ["plan", "payment_method"]
        )

        # System Metrics
        self.system_info = Info(
            "system_info",
            "System information"
        )

        self.memory_usage_bytes = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes"
        )

        self.cpu_usage_percent = Gauge(
            "cpu_usage_percent",
            "CPU usage percentage"
        )

        # Error Metrics
        self.errors_total = Counter(
            "errors_total",
            "Total errors",
            ["type", "endpoint", "severity"]
        )

        # Background Task Metrics
        self.background_tasks_total = Counter(
            "background_tasks_total",
            "Total background tasks",
            ["task_type", "status"]
        )

        self.background_task_duration_seconds = Histogram(
            "background_task_duration_seconds",
            "Background task duration in seconds",
            ["task_type"],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
        )

        # Queue Metrics
        self.queue_size = Gauge(
            "queue_size",
            "Queue size",
            ["queue_name"]
        )

        self.queue_processing_rate = Counter(
            "queue_processing_rate",
            "Queue processing rate",
            ["queue_name", "status"]
        )

    def initialize(self, app: FastAPI) -> None:
        """Initialize Prometheus monitoring for FastAPI application."""
        try:
            # Set system info
            self.system_info.info({
                "app_name": monitoring_config.APP_NAME,
                "version": monitoring_config.APP_VERSION,
                "environment": monitoring_config.SENTRY_ENVIRONMENT,
            })

            # Setup FastAPI instrumentator
            instrumentator = Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True,
                should_respect_env_var=True,
                should_instrument_requests_inprogress=True,
                excluded_handlers=["/metrics", "/health", "/docs", "/openapi.json"],
                env_var_name="ENABLE_METRICS",
            )

            # Add custom metrics
            instrumentator.add(
                metrics.request_size(
                    should_include_handler=True,
                    should_include_method=True,
                    should_include_status=True,
                )
            )

            instrumentator.add(
                metrics.response_size(
                    should_include_handler=True,
                    should_include_method=True,
                    should_include_status=True,
                )
            )

            instrumentator.add(
                metrics.latency(
                    should_include_handler=True,
                    should_include_method=True,
                    should_include_status=True,
                )
            )

            # Instrument the app
            instrumentator.instrument(app).expose(app, include_in_schema=False)

            self.initialized = True
            logger.info("Prometheus monitoring initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Prometheus monitoring: {e}")
            self.initialized = False

    def record_http_request(self, method: str, endpoint: str, status: int, duration: float, user_id: str = None) -> None:
        """Record HTTP request metrics."""
        if not self.initialized:
            return

        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status,
                user_id=user_id or "anonymous"
            ).inc()

            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).observe(duration)

        except Exception as e:
            logger.error(f"Failed to record HTTP request metrics: {e}")

    def record_ai_request(self, provider: str, task_type: str, status: str, duration: float, user_id: str = None) -> None:
        """Record AI service request metrics."""
        if not self.initialized:
            return

        try:
            self.ai_requests_total.labels(
                provider=provider,
                task_type=task_type,
                status=status,
                user_id=user_id or "anonymous"
            ).inc()

            self.ai_request_duration_seconds.labels(
                provider=provider,
                task_type=task_type
            ).observe(duration)

        except Exception as e:
            logger.error(f"Failed to record AI request metrics: {e}")

    def record_ai_tokens(self, provider: str, task_type: str, token_type: str, tokens: int, user_id: str = None) -> None:
        """Record AI token usage metrics."""
        if not self.initialized:
            return

        try:
            self.ai_tokens_used_total.labels(
                provider=provider,
                task_type=task_type,
                token_type=token_type,
                user_id=user_id or "anonymous"
            ).inc(tokens)

        except Exception as e:
            logger.error(f"Failed to record AI token metrics: {e}")

    def record_ai_cost(self, provider: str, task_type: str, cost: float, user_id: str = None) -> None:
        """Record AI cost metrics."""
        if not self.initialized:
            return

        try:
            self.ai_cost_total.labels(
                provider=provider,
                task_type=task_type,
                user_id=user_id or "anonymous"
            ).inc(cost)

        except Exception as e:
            logger.error(f"Failed to record AI cost metrics: {e}")

    def record_db_operation(self, operation: str, table: str, status: str, duration: float) -> None:
        """Record database operation metrics."""
        if not self.initialized:
            return

        try:
            self.db_operations_total.labels(
                operation=operation,
                table=table,
                status=status
            ).inc()

            self.db_operation_duration_seconds.labels(
                operation=operation,
                table=table
            ).observe(duration)

        except Exception as e:
            logger.error(f"Failed to record database operation metrics: {e}")

    def record_cache_operation(self, operation: str, status: str) -> None:
        """Record cache operation metrics."""
        if not self.initialized:
            return

        try:
            self.cache_operations_total.labels(
                operation=operation,
                status=status
            ).inc()

        except Exception as e:
            logger.error(f"Failed to record cache operation metrics: {e}")

    def set_cache_hit_ratio(self, cache_type: str, ratio: float) -> None:
        """Set cache hit ratio metric."""
        if not self.initialized:
            return

        try:
            self.cache_hit_ratio.labels(cache_type=cache_type).set(ratio)

        except Exception as e:
            logger.error(f"Failed to set cache hit ratio metric: {e}")

    def set_active_users(self, count: int) -> None:
        """Set active users metric."""
        if not self.initialized:
            return

        try:
            self.active_users.set(count)

        except Exception as e:
            logger.error(f"Failed to set active users metric: {e}")

    def record_user_session(self, status: str) -> None:
        """Record user session metric."""
        if not self.initialized:
            return

        try:
            self.user_sessions_total.labels(status=status).inc()

        except Exception as e:
            logger.error(f"Failed to record user session metric: {e}")

    def record_subscription(self, plan: str, status: str) -> None:
        """Record subscription metric."""
        if not self.initialized:
            return

        try:
            self.subscriptions_total.labels(plan=plan, status=status).inc()

        except Exception as e:
            logger.error(f"Failed to record subscription metric: {e}")

    def record_revenue(self, plan: str, payment_method: str, amount: float) -> None:
        """Record revenue metric."""
        if not self.initialized:
            return

        try:
            self.revenue_total.labels(
                plan=plan,
                payment_method=payment_method
            ).inc(amount)

        except Exception as e:
            logger.error(f"Failed to record revenue metric: {e}")

    def record_error(self, error_type: str, endpoint: str, severity: str) -> None:
        """Record error metric."""
        if not self.initialized:
            return

        try:
            self.errors_total.labels(
                type=error_type,
                endpoint=endpoint,
                severity=severity
            ).inc()

        except Exception as e:
            logger.error(f"Failed to record error metric: {e}")

    def record_background_task(self, task_type: str, status: str, duration: float) -> None:
        """Record background task metric."""
        if not self.initialized:
            return

        try:
            self.background_tasks_total.labels(
                task_type=task_type,
                status=status
            ).inc()

            if status == "completed":
                self.background_task_duration_seconds.labels(
                    task_type=task_type
                ).observe(duration)

        except Exception as e:
            logger.error(f"Failed to record background task metric: {e}")

    def set_queue_size(self, queue_name: str, size: int) -> None:
        """Set queue size metric."""
        if not self.initialized:
            return

        try:
            self.queue_size.labels(queue_name=queue_name).set(size)

        except Exception as e:
            logger.error(f"Failed to set queue size metric: {e}")

    def record_queue_processing(self, queue_name: str, status: str) -> None:
        """Record queue processing metric."""
        if not self.initialized:
            return

        try:
            self.queue_processing_rate.labels(
                queue_name=queue_name,
                status=status
            ).inc()

        except Exception as e:
            logger.error(f"Failed to record queue processing metric: {e}")

    def get_metrics(self) -> str:
        """Get Prometheus metrics as string."""
        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return ""


# Global Prometheus service instance
prometheus_service = PrometheusService()


def get_prometheus_service() -> PrometheusService:
    """Get the global Prometheus service instance."""
    return prometheus_service


def setup_prometheus_middleware(app: FastAPI) -> None:
    """Setup Prometheus middleware for FastAPI application."""
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        """Prometheus middleware for request tracking."""
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            prometheus_service.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration,
                user_id=getattr(request.state, "user_id", None)
            )

            return response

        except Exception as exc:
            duration = time.time() - start_time

            # Record error metrics
            prometheus_service.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status=500,
                duration=duration,
                user_id=getattr(request.state, "user_id", None)
            )

            prometheus_service.record_error(
                error_type=exc.__class__.__name__,
                endpoint=request.url.path,
                severity="high"
            )

            raise
