from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union, Dict, Any
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Union[Dict[str, Any], None] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(APIError):
    """Exception for validation errors."""
    def __init__(self, message: str, details: Union[Dict[str, Any], None] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(APIError):
    """Exception for authentication errors."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(APIError):
    """Exception for authorization errors."""
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundError(APIError):
    """Exception for not found errors."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for all exceptions."""
    error_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
    
    if isinstance(exc, APIError):
        status_code = exc.status_code
        error_response = {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "error_id": error_id
            }
        }
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        error_response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": {"validation_errors": exc.errors()},
                "error_id": error_id
            }
        }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "error_id": error_id
            }
        }

    # Log the error with full context
    log_context = {
        "error_id": error_id,
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "status_code": status_code,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc()
    }
    
    if status_code >= 500:
        logger.error("Server error occurred", extra=log_context)
    else:
        logger.warning("Client error occurred", extra=log_context)

    return JSONResponse(
        status_code=status_code,
        content=error_response
    ) 