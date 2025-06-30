from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "You've hit the rate limit. Please slow down and try again shortly.",
            "retry_after": getattr(exc, "headers", {}).get(
                "Retry-After", "60"
            ),  # optional
        },
        headers=getattr(exc, "headers", {}),  # preserve rate-limit headers if present
    )
