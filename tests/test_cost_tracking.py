from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cost_tracking import CostTracker, cost_tracking_service


class TestCostTracker:
    """Test cost tracking service functionality."""

    def test_pricing_calculation(self):
        """Test OpenAI pricing calculation."""
        service = CostTracker()
        
        # Test GPT-4 pricing
        assert service.pricing["gpt-4"]["input"] == 0.03
        assert service.pricing["gpt-4"]["output"] == 0.06
        
        # Test GPT-3.5 pricing
        assert service.pricing["gpt-3.5-turbo"]["input"] == 0.001
        assert service.pricing["gpt-3.5-turbo"]["output"] == 0.002

    @patch('services.cost_tracking.supabase_client')
    def test_track_openai_usage(self, mock_supabase):
        """Test OpenAI usage tracking."""
        service = CostTracker()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = None
        
        service.track_openai_usage(
            user_id="user123",
            model="gpt-3.5-turbo", 
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )
        
        # Verify supabase was called
        mock_supabase.table.assert_called_with("openai_usage")
        # Verify supabase was called (method calls both openai_usage and usage_totals tables)
        assert mock_supabase.table.called

    def test_get_user_usage_summary_structure(self):
        """Test usage summary structure."""
        service = CostTracker()
        
        with patch('services.cost_tracking.supabase_client') as mock_supabase:
            # Mock empty responses
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            summary = service.get_user_usage_summary("user123")
            
            # Check structure
            assert "daily" in summary
            assert "monthly" in summary
            assert "limits" in summary
            assert summary["limits"]["daily_limit_usd"] == 10.0
            assert summary["limits"]["monthly_limit_usd"] == 100.0

    def test_check_usage_limits_structure(self):
        """Test usage limits check structure."""
        service = CostTracker()
        
        with patch.object(service, 'get_user_usage_summary') as mock_summary:
            mock_summary.return_value = {
                "daily": {"total_cost_usd": 5.0},
                "monthly": {"total_cost_usd": 50.0},
                "limits": {"daily_limit_usd": 10.0, "monthly_limit_usd": 100.0}
            }
            
            result = service.check_usage_limits("user123")
            
            assert "can_use" in result
            assert "daily_exceeded" in result
            assert "monthly_exceeded" in result
            assert result["can_use"] is True
            assert result["daily_exceeded"] is False
            assert result["monthly_exceeded"] is False

    def test_check_usage_limits_exceeded(self):
        """Test usage limits when exceeded."""
        service = CostTracker()
        
        with patch.object(service, 'get_user_usage_summary') as mock_summary:
            mock_summary.return_value = {
                "daily": {"total_cost_usd": 15.0},  # Exceeds 10.0 limit
                "monthly": {"total_cost_usd": 150.0},  # Exceeds 100.0 limit
                "limits": {"daily_limit_usd": 10.0, "monthly_limit_usd": 100.0}
            }
            
            result = service.check_usage_limits("user123")
            
            assert result["can_use"] is False
            assert result["daily_exceeded"] is True
            assert result["monthly_exceeded"] is True