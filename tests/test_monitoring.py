from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from services.monitoring import MonitoringService


class TestMonitoringService:
    """Test monitoring service functionality."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance."""
        return MonitoringService()

    def test_init(self, monitoring_service):
        """Test monitoring service initialization."""
        assert monitoring_service.metrics == {}
        assert monitoring_service.alerts == []

    def test_record_metric(self, monitoring_service):
        """Test recording metrics."""
        monitoring_service.record_metric("cpu_usage", 75.5)
        monitoring_service.record_metric("memory_usage", 60.2)
        
        assert "cpu_usage" in monitoring_service.metrics
        assert "memory_usage" in monitoring_service.metrics
        assert monitoring_service.metrics["cpu_usage"][-1] == 75.5

    def test_get_metric_stats(self, monitoring_service):
        """Test getting metric statistics."""
        # Record some metrics
        monitoring_service.record_metric("response_time", 100)
        monitoring_service.record_metric("response_time", 150)
        monitoring_service.record_metric("response_time", 200)
        
        stats = monitoring_service.get_metric_stats("response_time")
        
        assert stats["count"] == 3
        assert stats["avg"] == 150.0
        assert stats["min"] == 100
        assert stats["max"] == 200

    def test_get_metric_stats_empty(self, monitoring_service):
        """Test getting stats for non-existent metric."""
        stats = monitoring_service.get_metric_stats("nonexistent")
        
        assert stats is None

    def test_check_thresholds(self, monitoring_service):
        """Test threshold checking."""
        # Set up thresholds
        thresholds = {
            "cpu_usage": {"max": 80, "min": 0},
            "memory_usage": {"max": 90, "min": 0}
        }
        
        # Record metrics that exceed thresholds
        monitoring_service.record_metric("cpu_usage", 85)
        monitoring_service.record_metric("memory_usage", 95)
        
        alerts = monitoring_service.check_thresholds(thresholds)
        
        assert len(alerts) == 2
        assert any("cpu_usage" in alert for alert in alerts)
        assert any("memory_usage" in alert for alert in alerts)

    def test_get_system_health(self, monitoring_service):
        """Test system health check."""
        # Record some metrics
        monitoring_service.record_metric("cpu_usage", 50)
        monitoring_service.record_metric("memory_usage", 40)
        monitoring_service.record_metric("disk_usage", 30)
        
        health = monitoring_service.get_system_health()
        
        assert "cpu_usage" in health
        assert "memory_usage" in health
        assert "disk_usage" in health
        assert health["status"] in ["healthy", "warning", "critical"]

    @patch('services.monitoring.logger')
    def test_log_alert(self, mock_logger, monitoring_service):
        """Test alert logging."""
        monitoring_service.log_alert("High CPU usage detected", "warning")
        
        mock_logger.warning.assert_called_once()

    def test_clear_metrics(self, monitoring_service):
        """Test clearing metrics."""
        monitoring_service.record_metric("test_metric", 100)
        monitoring_service.clear_metrics()
        
        assert len(monitoring_service.metrics) == 0

    def test_export_metrics(self, monitoring_service):
        """Test metrics export."""
        monitoring_service.record_metric("api_calls", 1000)
        monitoring_service.record_metric("response_time", 250)
        
        exported = monitoring_service.export_metrics()
        
        assert "api_calls" in exported
        assert "response_time" in exported
        assert len(exported["api_calls"]) == 1
        assert exported["api_calls"][0] == 1000