from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable
import uuid
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: set = None,
        exclude_methods: set = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024 * 1024,  # 1MB
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or set()
        self.exclude_methods = exclude_methods or set()
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths/methods
        if (
            request.url.path in self.exclude_paths
            or request.method in self.exclude_methods
        ):
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Log request
        request_body = None
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    request_body = body.decode()
            except Exception as e:
                logger.warning(f"Failed to read request body: {str(e)}")

        # Log request details
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_body": request_body if self.log_request_body else None,
        }

        logger.info("Incoming request", extra={"request_data": log_data})

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            response_body = None
            if self.log_response_body:
                try:
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    if len(body) <= self.max_body_size:
                        response_body = body.decode()
                    response.body_iterator = iter([body])
                except Exception as e:
                    logger.warning(f"Failed to read response body: {str(e)}")

            # Log response details
            response_log = {
                "request_id": request_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "response_body": response_body if self.log_response_body else None,
            }

            # Log based on status code
            if response.status_code >= 500:
                logger.error(
                    "Server error response", extra={"response_data": response_log}
                )
            elif response.status_code >= 400:
                logger.warning(
                    "Client error response", extra={"response_data": response_log}
                )
            else:
                logger.info(
                    "Successful response", extra={"response_data": response_log}
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                },
                exc_info=True,
            )
            raise


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add request context to logging
        context = {
            "request_id": str(uuid.uuid4()),
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        }

        # Create a context filter
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.request_id = context["request_id"]
                record.path = context["path"]
                record.method = context["method"]
                record.client_ip = context["client_ip"]
                return True

        # Add filter to logger
        logger.addFilter(ContextFilter())

        try:
            response = await call_next(request)
            return response
        finally:
            # Remove filter
            logger.removeFilter(ContextFilter())
