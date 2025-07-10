import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from middleware.error_handler import (
    APIError,
    ValidationError,
    AuthenticationError,
    create_error_response,
    error_handler,
    categorize_error,
)


class TestErrorHandlers:
    """Test error handling middleware."""

    def test_create_error_response_api_error(self):
        """Test error response creation for API errors."""
        request = MagicMock(spec=Request)
        exc = APIError("Test error", status_code=400, error_code="TEST_ERROR")
        error_id = "test-error-id"
        
        response = create_error_response(exc, error_id, request)
        
        assert "error" in response
        assert response["error"]["message"] == "Test error"
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["error_id"] == error_id

    def test_create_error_response_validation_error(self):
        """Test error response creation for validation errors."""
        request = MagicMock(spec=Request)
        
        # Create a mock validation error
        exc = RequestValidationError([{
            "loc": ("body", "name"),
            "msg": "field required",
            "type": "value_error.missing"
        }])
        error_id = "test-error-id"
        
        response = create_error_response(exc, error_id, request)
        
        assert "error" in response
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["error_id"] == error_id
        assert "validation_errors" in response["error"]["details"]

    @pytest.mark.asyncio
    async def test_error_handler_api_error(self):
        """Test error handler with API error."""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        exc = APIError("Test error", status_code=400)
        
        response = await error_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Handle different response body types
        content = json.loads(response.body)  # type: ignore[arg-type]
        assert content["error"]["message"] == "Test error"

    @pytest.mark.asyncio
    async def test_error_handler_general_exception(self):
        """Test error handler with general exception."""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}
        request.query_params = {}
        
        exc = Exception("Something went wrong")
        
        response = await error_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # Handle different response body types
        content = json.loads(response.body)  # type: ignore[arg-type]
        assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"

    def test_categorize_error_api_error(self):
        """Test error categorization for API errors."""
        exc = ValidationError("Test validation error")
        category = categorize_error(exc)
        
        assert category["category"] == "api_error"
        assert category["severity"] == "low"
        assert category["retryable"] is False

    def test_categorize_error_network_error(self):
        """Test error categorization for network errors."""
        exc = ConnectionError("Connection failed")
        category = categorize_error(exc)
        
        assert category["category"] == "network_error"
        assert category["severity"] == "medium"
        assert category["retryable"] is True

    def test_api_error_classes(self):
        """Test custom API error classes."""
        # Test ValidationError
        validation_err = ValidationError("Invalid data", {"field": "error"})
        assert validation_err.status_code == 422
        assert validation_err.error_code == "VALIDATION_ERROR"
        
        # Test AuthenticationError
        auth_err = AuthenticationError("Invalid token")
        assert auth_err.status_code == 401
        assert auth_err.error_code == "AUTHENTICATION_ERROR"