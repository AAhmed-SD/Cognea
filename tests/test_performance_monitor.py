import time
from unittest.mock import MagicMock, patch

import pytest

from services.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    @pytest.fixture
    def perf_monitor(self):
        """Create performance monitor instance."""
        return PerformanceMonitor()

    def test_start_timer(self, perf_monitor):
        """Test starting a timer."""
        timer_id = perf_monitor.start_timer("test_operation")
        
        assert timer_id is not None
        assert "test_operation" in perf_monitor.timers
        assert timer_id in perf_monitor.timers["test_operation"]

    def test_end_timer(self, perf_monitor):
        """Test ending a timer."""
        timer_id = perf_monitor.start_timer("test_operation")
        time.sleep(0.01)  # Small delay
        duration = perf_monitor.end_timer("test_operation", timer_id)
        
        assert duration > 0
        assert timer_id not in perf_monitor.timers.get("test_operation", {})

    def test_record_metric(self, perf_monitor):
        """Test recording metrics."""
        perf_monitor.record_metric("response_time", 0.5)
        perf_monitor.record_metric("response_time", 0.3)
        
        assert "response_time" in perf_monitor.metrics
        assert len(perf_monitor.metrics["response_time"]) == 2

    def test_get_stats(self, perf_monitor):
        """Test getting statistics."""
        # Record some metrics
        perf_monitor.record_metric("response_time", 0.1)
        perf_monitor.record_metric("response_time", 0.2)
        perf_monitor.record_metric("response_time", 0.3)
        
        stats = perf_monitor.get_stats("response_time")
        
        assert stats["count"] == 3
        assert stats["avg"] == 0.2
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3

    def test_get_stats_empty(self, perf_monitor):
        """Test getting stats for non-existent metric."""
        stats = perf_monitor.get_stats("nonexistent")
        
        assert stats["count"] == 0
        assert stats["avg"] == 0
        assert stats["min"] == 0
        assert stats["max"] == 0

    def test_clear_metrics(self, perf_monitor):
        """Test clearing metrics."""
        perf_monitor.record_metric("test_metric", 1.0)
        perf_monitor.clear_metrics()
        
        assert len(perf_monitor.metrics) == 0

    @patch('services.performance_monitor.logger')
    def test_log_performance(self, mock_logger, perf_monitor):
        """Test performance logging."""
        perf_monitor.record_metric("api_response", 0.5)
        perf_monitor.log_performance("api_response")
        
        mock_logger.info.assert_called_once()