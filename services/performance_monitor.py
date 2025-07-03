"""
Performance Monitoring System
- Real-time metrics collection
- Performance profiling
- Resource monitoring
- Alerting system
- Optimization recommendations
- Performance dashboards
"""

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import psutil
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    tags: dict[str, str]
    metadata: dict[str, Any]


@dataclass
class Alert:
    id: str
    name: str
    severity: str  # info, warning, error, critical
    message: str
    timestamp: datetime
    metric_type: str
    threshold: float
    current_value: float
    resolved: bool = False
    resolved_at: datetime | None = None


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        collection_interval: int = 30,
        retention_days: int = 30,
        alert_thresholds: dict[str, dict[str, float]] = None,
    ):
        self.redis_url = redis_url
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self.alert_thresholds = alert_thresholds or {}

        # Redis connection
        self.redis = None

        # Monitoring state
        self.running = False
        self.collection_task = None
        self.cleanup_task = None

        # Metrics storage
        self.metrics_buffer = deque(maxlen=1000)
        self.alert_handlers: list[Callable] = []

        # Performance counters
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)

        # System metrics
        self.cpu_usage = deque(maxlen=100)
        self.memory_usage = deque(maxlen=100)
        self.disk_usage = deque(maxlen=100)
        self.network_io = deque(maxlen=100)

    async def start(self):
        """Start performance monitoring"""
        try:
            # Connect to Redis
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()

            # Start monitoring tasks
            self.running = True
            self.collection_task = asyncio.create_task(self._collect_metrics())
            self.cleanup_task = asyncio.create_task(self._cleanup_old_metrics())

            logger.info("Performance monitor started")

        except Exception as e:
            logger.error(f"Failed to start performance monitor: {e}")
            raise

    async def stop(self):
        """Stop performance monitoring"""
        self.running = False

        if self.collection_task:
            self.collection_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        if self.collection_task or self.cleanup_task:
            await asyncio.gather(
                self.collection_task, self.cleanup_task, return_exceptions=True
            )

        if self.redis:
            await self.redis.close()

        logger.info("Performance monitor stopped")

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler function"""
        self.alert_handlers.append(handler)

    async def record_metric(
        self,
        metric_type: str,
        value: float,
        unit: str = "",
        tags: dict[str, str] = None,
        metadata: dict[str, Any] = None,
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
            metadata=metadata or {},
        )

        # Add to buffer
        self.metrics_buffer.append(metric)

        # Check for alerts
        await self._check_alerts(metric)

        # Store in Redis if buffer is full
        if len(self.metrics_buffer) >= 100:
            await self._flush_metrics()

    async def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics"""
        self.request_count += 1
        self.response_times.append(duration)

        if status_code >= 400:
            self.error_count += 1

        await self.record_metric(
            "http_request_duration",
            duration,
            "seconds",
            {
                "method": method,
                "path": path,
                "status_code": str(status_code),
            },
        )

        await self.record_metric(
            "http_requests_total",
            1,
            "requests",
            {
                "method": method,
                "path": path,
                "status_code": str(status_code),
            },
        )

    async def record_database_query(self, query_type: str, table: str, duration: float):
        """Record database query metrics"""
        await self.record_metric(
            "database_query_duration",
            duration,
            "seconds",
            {
                "query_type": query_type,
                "table": table,
            },
        )

    async def record_cache_operation(self, operation: str, hit: bool, duration: float):
        """Record cache operation metrics"""
        await self.record_metric(
            "cache_operation_duration",
            duration,
            "seconds",
            {
                "operation": operation,
                "hit": str(hit).lower(),
            },
        )

    async def record_ai_operation(
        self, operation: str, tokens_used: int, duration: float
    ):
        """Record AI operation metrics"""
        await self.record_metric(
            "ai_operation_duration",
            duration,
            "seconds",
            {
                "operation": operation,
            },
        )

        await self.record_metric(
            "ai_tokens_used",
            tokens_used,
            "tokens",
            {
                "operation": operation,
            },
        )

    async def _collect_metrics(self):
        """Collect system metrics periodically"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.append(cpu_percent)
                await self.record_metric("cpu_usage", cpu_percent, "percent")

                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self.memory_usage.append(memory_percent)
                await self.record_metric("memory_usage", memory_percent, "percent")
                await self.record_metric("memory_available", memory.available, "bytes")

                # Disk usage
                disk = psutil.disk_usage("/")
                disk_percent = (disk.used / disk.total) * 100
                self.disk_usage.append(disk_percent)
                await self.record_metric("disk_usage", disk_percent, "percent")
                await self.record_metric("disk_available", disk.free, "bytes")

                # Network I/O
                network = psutil.net_io_counters()
                await self.record_metric(
                    "network_bytes_sent", network.bytes_sent, "bytes"
                )
                await self.record_metric(
                    "network_bytes_recv", network.bytes_recv, "bytes"
                )

                # Application metrics
                if self.response_times:
                    avg_response_time = sum(self.response_times) / len(
                        self.response_times
                    )
                    await self.record_metric(
                        "avg_response_time", avg_response_time, "seconds"
                    )

                await self.record_metric(
                    "request_count", self.request_count, "requests"
                )
                await self.record_metric("error_count", self.error_count, "errors")

                if self.request_count > 0:
                    error_rate = (self.error_count / self.request_count) * 100
                    await self.record_metric("error_rate", error_rate, "percent")

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _flush_metrics(self):
        """Flush metrics buffer to Redis"""
        if not self.metrics_buffer:
            return

        try:
            metrics_data = []
            for metric in self.metrics_buffer:
                metrics_data.append(metric.to_dict())

            # Store in Redis with timestamp-based key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            key = f"metrics:{timestamp}"

            await self.redis.setex(
                key,
                self.retention_days * 24 * 3600,  # TTL in seconds
                json.dumps(metrics_data),
            )

            # Clear buffer
            self.metrics_buffer.clear()

        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        while self.running:
            try:
                # Get all metric keys
                keys = await self.redis.keys("metrics:*")

                cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)
                cutoff_timestamp = cutoff_time.strftime("%Y%m%d_%H%M%S")

                # Delete old metrics
                for key in keys:
                    timestamp_str = key.split(":")[1]
                    if timestamp_str < cutoff_timestamp:
                        await self.redis.delete(key)

                await asyncio.sleep(3600)  # Run cleanup every hour

            except Exception as e:
                logger.error(f"Error cleaning up metrics: {e}")
                await asyncio.sleep(3600)

    async def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        thresholds = self.alert_thresholds.get(metric.metric_type, {})

        for severity, threshold in thresholds.items():
            if metric.value > threshold:
                alert = Alert(
                    id=f"{metric.metric_type}_{int(time.time())}",
                    name=f"{metric.metric_type} threshold exceeded",
                    severity=severity,
                    message=f"{metric.metric_type} exceeded {threshold} {metric.unit} (current: {metric.value})",
                    timestamp=metric.timestamp,
                    metric_type=metric.metric_type,
                    threshold=threshold,
                    current_value=metric.value,
                )

                await self._trigger_alert(alert)

    async def _trigger_alert(self, alert: Alert):
        """Trigger alert handlers"""
        # Store alert in Redis
        await self.redis.hset(f"alert:{alert.id}", mapping=asdict(alert))

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        logger.warning(f"Alert triggered: {alert.message}")

    async def get_metrics(
        self,
        metric_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
    ) -> list[PerformanceMetric]:
        """Get metrics from storage"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=1)
            if not end_time:
                end_time = datetime.utcnow()

            # Get metric keys in time range
            start_timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            end_timestamp = end_time.strftime("%Y%m%d_%H%M%S")

            keys = await self.redis.keys("metrics:*")
            filtered_keys = [
                key
                for key in keys
                if start_timestamp <= key.split(":")[1] <= end_timestamp
            ]

            metrics = []
            for key in filtered_keys[:limit]:
                data = await self.redis.get(key)
                if data:
                    metrics_data = json.loads(data)
                    for metric_data in metrics_data:
                        if not metric_type or metric_data["metric_type"] == metric_type:
                            metric = PerformanceMetric(**metric_data)
                            metrics.append(metric)

            return sorted(metrics, key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return []

    async def get_alerts(
        self,
        severity: str = None,
        resolved: bool = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alerts from storage"""
        try:
            keys = await self.redis.keys("alert:*")
            alerts = []

            for key in keys[:limit]:
                data = await self.redis.hgetall(key)
                if data:
                    alert = Alert(**data)
                    if severity and alert.severity != severity:
                        continue
                    if resolved is not None and alert.resolved != resolved:
                        continue
                    alerts.append(alert)

            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []

    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        try:
            alert_data = await self.redis.hgetall(f"alert:{alert_id}")
            if alert_data:
                alert = Alert(**alert_data)
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                await self.redis.hset(f"alert:{alert_id}", mapping=asdict(alert))
                return True
            return False
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary"""
        summary = {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": 0,
            "avg_response_time": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
        }

        if self.request_count > 0:
            summary["error_rate"] = (self.error_count / self.request_count) * 100

        if self.response_times:
            summary["avg_response_time"] = sum(self.response_times) / len(
                self.response_times
            )

        if self.cpu_usage:
            summary["cpu_usage"] = self.cpu_usage[-1]

        if self.memory_usage:
            summary["memory_usage"] = self.memory_usage[-1]

        if self.disk_usage:
            summary["disk_usage"] = self.disk_usage[-1]

        return summary

    async def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Get performance optimization recommendations"""
        recommendations = []

        try:
            # Get recent metrics
            metrics = await self.get_metrics(limit=1000)

            # Analyze response times
            response_times = [
                m.value for m in metrics if m.metric_type == "http_request_duration"
            ]

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > 1.0:
                    recommendations.append(
                        {
                            "type": "response_time",
                            "severity": "warning",
                            "message": f"Average response time is {avg_response_time:.2f}s, consider optimizing database queries or adding caching",
                            "metric": "http_request_duration",
                            "current_value": avg_response_time,
                            "recommended_threshold": 1.0,
                        }
                    )

            # Analyze error rates
            error_rates = [m.value for m in metrics if m.metric_type == "error_rate"]

            if error_rates:
                avg_error_rate = sum(error_rates) / len(error_rates)
                if avg_error_rate > 5.0:
                    recommendations.append(
                        {
                            "type": "error_rate",
                            "severity": "critical",
                            "message": f"Error rate is {avg_error_rate:.1f}%, investigate and fix issues",
                            "metric": "error_rate",
                            "current_value": avg_error_rate,
                            "recommended_threshold": 5.0,
                        }
                    )

            # Analyze resource usage
            cpu_usage = [m.value for m in metrics if m.metric_type == "cpu_usage"]

            if cpu_usage:
                avg_cpu = sum(cpu_usage) / len(cpu_usage)
                if avg_cpu > 80:
                    recommendations.append(
                        {
                            "type": "cpu_usage",
                            "severity": "warning",
                            "message": f"CPU usage is {avg_cpu:.1f}%, consider scaling or optimization",
                            "metric": "cpu_usage",
                            "current_value": avg_cpu,
                            "recommended_threshold": 80.0,
                        }
                    )

            memory_usage = [m.value for m in metrics if m.metric_type == "memory_usage"]

            if memory_usage:
                avg_memory = sum(memory_usage) / len(memory_usage)
                if avg_memory > 85:
                    recommendations.append(
                        {
                            "type": "memory_usage",
                            "severity": "warning",
                            "message": f"Memory usage is {avg_memory:.1f}%, consider increasing memory or optimizing",
                            "metric": "memory_usage",
                            "current_value": avg_memory,
                            "recommended_threshold": 85.0,
                        }
                    )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


async def setup_performance_monitoring():
    """Setup global performance monitoring"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start()
    return _performance_monitor


# Performance monitoring decorators
def monitor_performance(metric_type: str, tags: dict[str, str] = None):
    """Decorator to monitor function performance"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                await performance_monitor.record_metric(
                    metric_type,
                    duration,
                    "seconds",
                    tags or {},
                )

                return result
            except Exception as e:
                duration = time.time() - start_time
                await performance_monitor.record_metric(
                    f"{metric_type}_error",
                    duration,
                    "seconds",
                    tags or {},
                    {"error": str(e)},
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record metric asynchronously
                asyncio.create_task(
                    performance_monitor.record_metric(
                        metric_type,
                        duration,
                        "seconds",
                        tags or {},
                    )
                )

                return result
            except Exception as e:
                duration = time.time() - start_time
                asyncio.create_task(
                    performance_monitor.record_metric(
                        f"{metric_type}_error",
                        duration,
                        "seconds",
                        tags or {},
                        {"error": str(e)},
                    )
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
