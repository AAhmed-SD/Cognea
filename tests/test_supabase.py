from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from supabase import Client

from services.supabase import (
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    get_supabase_client,
    get_supabase_service_client,
    supabase_client,
    test_connection,
)


class TestSupabaseConfiguration:
    """Test Supabase configuration and constants"""

    def test_supabase_constants_exist(self) -> None:
        """Test that Supabase constants are defined"""
        assert SUPABASE_URL is not None
        assert SUPABASE_ANON_KEY is not None
        # SUPABASE_SERVICE_ROLE_KEY might be None in some environments

    def test_supabase_client_exists(self) -> None:
        """Test that supabase_client is created"""
        assert supabase_client is not None
        assert isinstance(supabase_client, Client)


class TestGetSupabaseClient:
    """Test get_supabase_client function"""

    def test_get_supabase_client(self) -> None:
        """Test getting the Supabase client"""
        client = get_supabase_client()

        assert client is not None
        assert isinstance(client, Client)
        assert client == supabase_client  # Should return the same instance

    def test_get_supabase_client_returns_same_instance(self) -> None:
        """Test that get_supabase_client returns the same instance"""
        client1 = get_supabase_client()
        client2 = get_supabase_client()

        assert client1 is client2  # Should be the same object


class TestGetSupabaseServiceClient:
    """Test get_supabase_service_client function"""

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", "test_service_key")
    @patch("services.supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("services.supabase.create_client")
    def test_get_supabase_service_client_success(self, mock_create_client) -> None:
        """Test getting service client with valid service key"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        client = get_supabase_service_client()

        assert client is not None
        assert isinstance(client, Client)
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co", "test_service_key"
        )

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", None)
    def test_get_supabase_service_client_no_key(self) -> None:
        """Test getting service client without service key"""
        with pytest.raises(
            ValueError,
            match="SUPABASE_SERVICE_ROLE_KEY environment variable must be set for admin operations",
        ):
            get_supabase_service_client()

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", "")
    def test_get_supabase_service_client_empty_key(self) -> None:
        """Test getting service client with empty service key"""
        with pytest.raises(
            ValueError,
            match="SUPABASE_SERVICE_ROLE_KEY environment variable must be set for admin operations",
        ):
            get_supabase_service_client()


class TestTestConnection:
    """Test test_connection function"""

    @patch("services.supabase.supabase_client")
    def test_test_connection_success(self, mock_client) -> None:
        """Test successful connection test"""
        # Mock the table query chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute

        with patch("builtins.print") as mock_print:
            result = test_connection()

            assert result is True
            mock_print.assert_called_once_with("✅ Supabase connection successful!")
            mock_client.table.assert_called_once_with("users")
            mock_table.select.assert_called_once_with("id")
            mock_select.limit.assert_called_once_with(1)
            mock_limit.execute.assert_called_once()

    @patch("services.supabase.supabase_client")
    def test_test_connection_failure(self, mock_client) -> None:
        """Test failed connection test"""
        # Mock the table query to raise an exception
        mock_client.table.side_effect = Exception("Connection failed")

        with patch("builtins.print") as mock_print:
            result = test_connection()

            assert result is False
            mock_print.assert_called_once_with(
                "❌ Supabase connection failed: Connection failed"
            )

    @patch("services.supabase.supabase_client")
    def test_test_connection_network_error(self, mock_client) -> None:
        """Test connection test with network error"""
        # Mock the table query to raise a network error
        mock_client.table.side_effect = ConnectionError("Network unreachable")

        with patch("builtins.print") as mock_print:
            result = test_connection()

            assert result is False
            mock_print.assert_called_once_with(
                "❌ Supabase connection failed: Network unreachable"
            )

    @patch("services.supabase.supabase_client")
    def test_test_connection_auth_error(self, mock_client) -> None:
        """Test connection test with authentication error"""
        # Mock the table query to raise an auth error
        mock_client.table.side_effect = Exception("Invalid API key")

        with patch("builtins.print") as mock_print:
            result = test_connection()

            assert result is False
            mock_print.assert_called_once_with(
                "❌ Supabase connection failed: Invalid API key"
            )


class TestSupabaseIntegration:
    """Integration tests for Supabase functionality"""

    def test_supabase_client_singleton_pattern(self) -> None:
        """Test that Supabase client follows singleton pattern"""
        client1 = get_supabase_client()
        client2 = get_supabase_client()

        # Should be the same instance
        assert client1 is client2
        assert id(client1) == id(client2)

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", "test_service_key")
    @patch("services.supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("services.supabase.create_client")
    def test_service_client_creation(self, mock_create_client) -> None:
        """Test service client creation with proper parameters"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        client = get_supabase_service_client()

        # Verify create_client was called with correct parameters
        mock_create_client.assert_called_once()
        call_args = mock_create_client.call_args
        assert call_args[0][0] == "https://test.supabase.co"  # URL
        assert call_args[0][1] == "test_service_key"  # Service key

    def test_supabase_configuration_validation(self) -> None:
        """Test that Supabase configuration is properly validated"""
        # These should be set by the security config
        assert SUPABASE_URL is not None
        assert SUPABASE_ANON_KEY is not None

        # Service key might be optional depending on environment
        # but the function should handle None gracefully
        if SUPABASE_SERVICE_ROLE_KEY is None:
            with pytest.raises(ValueError):
                get_supabase_service_client()


class TestSupabaseErrorHandling:
    """Test error handling in Supabase functions"""

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", "")
    def test_service_client_empty_string_key(self) -> None:
        """Test service client with empty string key"""
        with pytest.raises(
            ValueError,
            match="SUPABASE_SERVICE_ROLE_KEY environment variable must be set for admin operations",
        ):
            get_supabase_service_client()

    @patch("services.supabase.SUPABASE_SERVICE_ROLE_KEY", "   ")
    def test_service_client_whitespace_key(self) -> None:
        """Test service client with whitespace-only key"""
        # The function only checks for None, not empty/whitespace strings
        # So this should not raise an exception
        with patch("services.supabase.create_client") as mock_create_client:
            mock_client = MagicMock(spec=Client)
            mock_create_client.return_value = mock_client

            client = get_supabase_service_client()

            assert client is not None
            assert isinstance(client, Client)

    @patch("services.supabase.supabase_client")
    def test_connection_test_with_specific_exception(self, mock_client) -> None:
        """Test connection test with specific exception types"""
        test_cases = [
            (ConnectionError("Connection refused"), "Connection refused"),
            (TimeoutError("Request timeout"), "Request timeout"),
            (ValueError("Invalid configuration"), "Invalid configuration"),
            (Exception("Unknown error"), "Unknown error"),
        ]

        for exception, expected_message in test_cases:
            mock_client.table.side_effect = exception

            with patch("builtins.print") as mock_print:
                result = test_connection()

                assert result is False
                mock_print.assert_called_once_with(
                    f"❌ Supabase connection failed: {expected_message}"
                )

                # Reset for next iteration
                mock_print.reset_mock()
