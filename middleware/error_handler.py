from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union, Dict, Any, Optional
import logging
import traceback
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Union[Dict[str, Any], None] = None,
        retry_after: Optional[int] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.retry_after = retry_after
        super().__init__(message)


class ValidationError(APIError):
    """Exception for validation errors."""

    def __init__(self, message: str, details: Union[Dict[str, Any], None] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(APIError):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(APIError):
    """Exception for authorization errors."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class NotFoundError(APIError):
    """Exception for not found errors."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class RateLimitError(APIError):
    """Exception for rate limiting errors."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            retry_after=retry_after,
        )


class ServiceUnavailableError(APIError):
    """Exception for service unavailable errors."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
        )


class ExternalServiceError(APIError):
    """Exception for external service errors."""

    def __init__(self, service: str, message: str = "External service error"):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


def categorize_error(exc: Exception) -> Dict[str, Any]:
    """Categorize errors for better handling and monitoring."""
    error_info = {
        "category": "unknown",
        "severity": "medium",
        "retryable": False,
        "user_facing": True,
    }

    if isinstance(exc, APIError):
        error_info["category"] = "api_error"
        error_info["severity"] = "low" if exc.status_code < 500 else "high"
        error_info["retryable"] = exc.status_code in [429, 502, 503, 504]
        error_info["user_facing"] = True
    elif isinstance(exc, RequestValidationError):
        error_info["category"] = "validation_error"
        error_info["severity"] = "low"
        error_info["retryable"] = False
        error_info["user_facing"] = True
    elif isinstance(exc, (ConnectionError, TimeoutError)):
        error_info["category"] = "network_error"
        error_info["severity"] = "medium"
        error_info["retryable"] = True
        error_info["user_facing"] = False
    elif isinstance(exc, (ValueError, TypeError, AttributeError)):
        error_info["category"] = "programming_error"
        error_info["severity"] = "high"
        error_info["retryable"] = False
        error_info["user_facing"] = False
    elif isinstance(exc, (ImportError, ModuleNotFoundError)):
        error_info["category"] = "dependency_error"
        error_info["severity"] = "high"
        error_info["retryable"] = False
        error_info["user_facing"] = False
    else:
        error_info["category"] = "unexpected_error"
        error_info["severity"] = "high"
        error_info["retryable"] = False
        error_info["user_facing"] = False

    return error_info


def create_error_response(
    exc: Exception, error_id: str, request: Request, include_traceback: bool = False
) -> Dict[str, Any]:
    """Create a structured error response."""
    error_info = categorize_error(exc)

    if isinstance(exc, APIError):
        response = {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "error_id": error_id,
                "category": error_info["category"],
                "severity": error_info["severity"],
                "retryable": error_info["retryable"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

        if exc.retry_after:
            response["error"]["retry_after"] = exc.retry_after

    elif isinstance(exc, RequestValidationError):
        response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": {"validation_errors": exc.errors()},
                "error_id": error_id,
                "category": error_info["category"],
                "severity": error_info["severity"],
                "retryable": error_info["retryable"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    else:
        response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": (
                    "An unexpected error occurred"
                    if error_info["user_facing"]
                    else str(exc)
                ),
                "error_id": error_id,
                "category": error_info["category"],
                "severity": error_info["severity"],
                "retryable": error_info["retryable"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

        if include_traceback:
            response["error"]["traceback"] = traceback.format_exc()

    return response


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Enhanced global error handler for all exceptions."""
    error_id = str(uuid.uuid4())
    error_info = categorize_error(exc)

    # Determine status code
    if isinstance(exc, APIError):
        status_code = exc.status_code
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # Create structured error response
    include_traceback = (
        error_info["severity"] == "high" and not error_info["user_facing"]
    )
    error_response = create_error_response(exc, error_id, request, include_traceback)

    # Enhanced logging with structured data
    log_context = {
        "error_id": error_id,
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "status_code": status_code,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "category": error_info["category"],
        "severity": error_info["severity"],
        "retryable": error_info["retryable"],
        "user_facing": error_info["user_facing"],
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
    }

    # Add traceback for high severity errors
    if error_info["severity"] == "high":
        log_context["traceback"] = traceback.format_exc()

    # Log based on severity
    if error_info["severity"] == "high":
        logger.error("High severity error occurred", extra=log_context)
    elif error_info["severity"] == "medium":
        logger.warning("Medium severity error occurred", extra=log_context)
    else:
        logger.info("Low severity error occurred", extra=log_context)

    # Add retry-after header for rate limit errors
    headers = {}
    if isinstance(exc, APIError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=status_code, content=error_response, headers=headers
    )


def setup_error_handlers(app: FastAPI):
    """Setup error handlers for the FastAPI application."""
    app.add_exception_handler(Exception, error_handler)
    app.add_exception_handler(APIError, error_handler)
    app.add_exception_handler(RequestValidationError, error_handler)
    logger.info("Enhanced error handlers configured")


# Error tracking and alerting utilities
class ErrorTracker:
    """Utility for tracking and alerting on errors."""

    def __init__(self):
        self.error_counts = {}
        self.alert_thresholds = {
            "high": 5,  # Alert after 5 high severity errors
            "medium": 20,  # Alert after 20 medium severity errors
            "low": 100,  # Alert after 100 low severity errors
        }

    def track_error(self, error_info: Dict[str, Any]):
        """Track an error for monitoring purposes."""
        category = error_info["category"]
        severity = error_info["severity"]

        key = f"{category}:{severity}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Check if we should alert
        threshold = self.alert_thresholds.get(severity, 10)
        if self.error_counts[key] >= threshold:
            self._send_alert(category, severity, self.error_counts[key])

    def _send_alert(self, category: str, severity: str, count: int):
        """Send an alert for error threshold exceeded."""
        logger.critical(
            f"Error threshold exceeded: {category} ({severity}) - {count} errors",
            extra={
                "alert_type": "error_threshold",
                "category": category,
                "severity": severity,
                "count": count,
            },
        )
        # TODO: Integrate with external alerting service (e.g., Sentry, PagerDuty)


# Global error tracker instance
error_tracker = ErrorTracker()
