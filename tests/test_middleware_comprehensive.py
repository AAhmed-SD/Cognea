#!/usr/bin/env python3
"""Comprehensive tests for middleware modules."""

import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Any, Dict

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# Import middleware modules
from middleware.error_handler import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    categorize_error,
    create_error_response,
    error_handler,
    setup_error_handlers,
    ErrorTracker,
)


class TestAPIError:
    """Test API error classes."""

    def test_api_error_creation(self) -> None:
        """Test API error creation."""
        error = APIError("Test error", 400, "TEST_ERROR")
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.error_code == "TEST_ERROR"
        assert error.details == {}
        assert error.retry_after is None

    def test_api_error_with_details(self) -> None:
        """Test API error with details."""
        details = {"field": "value"}
        error = APIError("Test error", 400, "TEST_ERROR", details=details, retry_after=60)
        assert error.details == details
        assert error.retry_after == 60

    def test_validation_error(self) -> None:
        """Test validation error."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert error.status_code == 422
        assert error.error_code == "VALIDATION_ERROR"

    def test_authentication_error(self) -> None:
        """Test authentication error."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_ERROR"
        
        custom_error = AuthenticationError("Custom auth message")
        assert str(custom_error) == "Custom auth message"

    def test_authorization_error(self) -> None:
        """Test authorization error."""
        error = AuthorizationError()
        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_ERROR"

    def test_not_found_error(self) -> None:
        """Test not found error."""
        error = NotFoundError()
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"

    def test_rate_limit_error(self) -> None:
        """Test rate limit error."""
        error = RateLimitError()
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.retry_after == 60

    def test_service_unavailable_error(self) -> None:
        """Test service unavailable error."""
        error = ServiceUnavailableError()
        assert error.status_code == 503
        assert error.error_code == "SERVICE_UNAVAILABLE"

    def test_external_service_error(self) -> None:
        """Test external service error."""
        error = ExternalServiceError("TestService", "Connection failed")
        assert error.status_code == 502
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert "TestService" in str(error)
        assert error.details["service"] == "TestService"


class TestErrorCategorization:
    """Test error categorization."""

    def test_categorize_api_error_low_severity(self) -> None:
        """Test categorizing low severity API error."""
        error = ValidationError("Invalid input")
        category = categorize_error(error)
        
        assert category["category"] == "api_error"
        assert category["severity"] == "low"
        assert category["retryable"] is False
        assert category["user_facing"] is True

    def test_categorize_api_error_high_severity(self) -> None:
        """Test categorizing high severity API error."""
        error = APIError("Server error", 500)
        category = categorize_error(error)
        
        assert category["category"] == "api_error"
        assert category["severity"] == "high"
        assert category["user_facing"] is True

    def test_categorize_retryable_error(self) -> None:
        """Test categorizing retryable error."""
        error = RateLimitError()
        category = categorize_error(error)
        
        assert category["retryable"] is True

    def test_categorize_validation_error(self) -> None:
        """Test categorizing validation error."""
        error = RequestValidationError([])
        category = categorize_error(error)
        
        assert category["category"] == "validation_error"
        assert category["severity"] == "low"
        assert category["retryable"] is False

    def test_categorize_network_error(self) -> None:
        """Test categorizing network error."""
        error = ConnectionError("Network error")
        category = categorize_error(error)
        
        assert category["category"] == "network_error"
        assert category["severity"] == "medium"
        assert category["retryable"] is True
        assert category["user_facing"] is False

    def test_categorize_programming_error(self) -> None:
        """Test categorizing programming error."""
        error = ValueError("Invalid value")
        category = categorize_error(error)
        
        assert category["category"] == "programming_error"
        assert category["severity"] == "high"
        assert category["retryable"] is False
        assert category["user_facing"] is False

    def test_categorize_dependency_error(self) -> None:
        """Test categorizing dependency error."""
        error = ImportError("Module not found")
        category = categorize_error(error)
        
        assert category["category"] == "dependency_error"
        assert category["severity"] == "high"
        assert category["retryable"] is False

    def test_categorize_unexpected_error(self) -> None:
        """Test categorizing unexpected error."""
        error = Exception("Unknown error")
        category = categorize_error(error)
        
        assert category["category"] == "unexpected_error"
        assert category["severity"] == "high"
        assert category["retryable"] is False


class TestErrorResponse:
    """Test error response creation."""

    def test_create_api_error_response(self) -> None:
        """Test creating API error response."""
        error = ValidationError("Invalid input", {"field": "email"})
        error_id = str(uuid.uuid4())
        request = Mock()
        
        response = create_error_response(error, error_id, request)
        
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid input"
        assert response["error"]["details"] == {"field": "email"}
        assert response["error"]["error_id"] == error_id
        assert "timestamp" in response["error"]

    def test_create_validation_error_response(self) -> None:
        """Test creating validation error response."""
        error = RequestValidationError([{"loc": ["field"], "msg": "required"}])
        error_id = str(uuid.uuid4())
        request = Mock()
        
        response = create_error_response(error, error_id, request)
        
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid request data"
        assert "validation_errors" in response["error"]["details"]

    def test_create_generic_error_response(self) -> None:
        """Test creating generic error response."""
        error = Exception("Generic error")
        error_id = str(uuid.uuid4())
        request = Mock()
        
        response = create_error_response(error, error_id, request)
        
        assert response["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert response["error"]["error_id"] == error_id

    def test_create_error_response_with_traceback(self) -> None:
        """Test creating error response with traceback."""
        error = ValueError("Programming error")
        error_id = str(uuid.uuid4())
        request = Mock()
        
        response = create_error_response(error, error_id, request, include_traceback=True)
        
        assert "traceback" in response["error"]

    def test_create_error_response_with_retry_after(self) -> None:
        """Test creating error response with retry after."""
        error = RateLimitError("Too many requests", retry_after=120)
        error_id = str(uuid.uuid4())
        request = Mock()
        
        response = create_error_response(error, error_id, request)
        
        assert response["error"]["retry_after"] == 120


class TestErrorHandler:
    """Test error handler functionality."""

    @pytest.mark.asyncio
    async def test_error_handler_api_error(self) -> None:
        """Test error handler with API error."""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        error = ValidationError("Invalid input")
        
        response = await error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_error_handler_validation_error(self) -> None:
        """Test error handler with validation error."""
        request = Mock()
        request.url.path = "/test"
        request.method = "POST"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        error = RequestValidationError([])
        
        response = await error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_error_handler_generic_error(self) -> None:
        """Test error handler with generic error."""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        error = Exception("Generic error")
        
        response = await error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_error_handler_with_retry_after(self) -> None:
        """Test error handler with retry after header."""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        error = RateLimitError("Too many requests", retry_after=60)
        
        response = await error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_error_handler_no_client(self) -> None:
        """Test error handler when request has no client."""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.client = None
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        error = Exception("Test error")
        
        response = await error_handler(request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestErrorTracker:
    """Test error tracker functionality."""

    def test_error_tracker_init(self) -> None:
        """Test error tracker initialization."""
        tracker = ErrorTracker()
        assert tracker.error_counts == {}
        assert "high" in tracker.alert_thresholds
        assert "medium" in tracker.alert_thresholds
        assert "low" in tracker.alert_thresholds

    @patch('middleware.error_handler.logger')
    def test_track_error_below_threshold(self, mock_logger: Mock) -> None:
        """Test tracking error below threshold."""
        tracker = ErrorTracker()
        error_info = {
            "category": "validation_error",
            "severity": "low",
        }
        
        tracker.track_error(error_info)
        
        assert tracker.error_counts["validation_error:low"] == 1
        mock_logger.critical.assert_not_called()

    @patch('middleware.error_handler.logger')
    def test_track_error_above_threshold(self, mock_logger: Mock) -> None:
        """Test tracking error above threshold."""
        tracker = ErrorTracker()
        tracker.alert_thresholds["high"] = 1  # Set low threshold for testing
        
        error_info = {
            "category": "programming_error",
            "severity": "high",
        }
        
        tracker.track_error(error_info)
        
        assert tracker.error_counts["programming_error:high"] == 1
        mock_logger.critical.assert_called_once()

    def test_track_multiple_errors(self) -> None:
        """Test tracking multiple errors."""
        tracker = ErrorTracker()
        error_info = {
            "category": "api_error",
            "severity": "medium",
        }
        
        for _ in range(3):
            tracker.track_error(error_info)
        
        assert tracker.error_counts["api_error:medium"] == 3


class TestErrorHandlerIntegration:
    """Test error handler integration with FastAPI."""

    def test_setup_error_handlers(self) -> None:
        """Test setting up error handlers."""
        app = FastAPI()
        setup_error_handlers(app)
        
        # Verify that exception handlers are registered
        assert Exception in app.exception_handlers
        assert APIError in app.exception_handlers
        assert RequestValidationError in app.exception_handlers

    def test_error_handler_integration(self) -> None:
        """Test error handler integration with FastAPI."""
        app = FastAPI()
        setup_error_handlers(app)
        
        @app.get("/test-error")
        def test_error():
            pass
            raise ValidationError("Test validation error")
        
        client = TestClient(app)
        response = client.get("/test-error")
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_error_integration(self) -> None:
        """Test validation error integration."""
        app = FastAPI()
        setup_error_handlers(app)
        
        @app.post("/test-validation")
        def test_validation(item: dict):
            pass
            return item
        
        client = TestClient(app)
        response = client.post("/test-validation", json="invalid")
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_generic_error_integration(self) -> None:
        """Test generic error integration."""
        app = FastAPI()
        setup_error_handlers(app)
        
        @app.get("/test-generic-error")
        def test_generic_error():
            pass
            raise Exception("Generic error")
        
        client = TestClient(app)
        response = client.get("/test-generic-error")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestErrorHandlerEdgeCases:
    """Test error handler edge cases."""

    def test_api_error_inheritance(self) -> None:
        """Test that custom errors inherit from APIError properly."""
        errors = [
            ValidationError("test"),
            AuthenticationError("test"),
            AuthorizationError("test"),
            NotFoundError("test"),
            RateLimitError("test"),
            ServiceUnavailableError("test"),
            ExternalServiceError("service", "test"),
        ]
        
        for error in errors:
            assert isinstance(error, APIError)
            assert hasattr(error, "status_code")
            assert hasattr(error, "error_code")
            assert hasattr(error, "message")

    def test_error_response_structure(self) -> None:
        """Test that error responses have consistent structure."""
        errors = [
            ValidationError("test"),
            Exception("test"),
            RequestValidationError([]),
        ]
        
        for error in errors:
            error_id = str(uuid.uuid4())
            request = Mock()
            response = create_error_response(error, error_id, request)
            
            assert "error" in response
            assert "code" in response["error"]
            assert "message" in response["error"]
            assert "error_id" in response["error"]
            assert "timestamp" in response["error"]
            assert "category" in response["error"]
            assert "severity" in response["error"]

    @pytest.mark.asyncio
    async def test_error_handler_logging(self) -> None:
        """Test that error handler logs appropriately."""
        with patch('middleware.error_handler.logger') as mock_logger:
            request = Mock()
            request.url.path = "/test"
            request.method = "GET"
            request.client.host = "127.0.0.1"
            request.headers = {"user-agent": "test"}
            request.query_params = {}
            
            # Test high severity error
            error = ValueError("Programming error")
            await error_handler(request, error)
            mock_logger.error.assert_called_once()
            
            # Reset mock
            mock_logger.reset_mock()
            
            # Test low severity error
            error = ValidationError("Validation error")
            await error_handler(request, error)
            mock_logger.info.assert_called_once()