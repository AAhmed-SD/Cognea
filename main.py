import logging.config
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Load environment variables from .env file
load_dotenv()

from middleware.error_handler import error_handler, APIError
from middleware.logging import LoggingMiddleware, RequestContextMiddleware
from middleware.rate_limit import RateLimiter
from services.redis_client import get_redis_client
from services.monitoring import monitoring_service

from routes.diary import router as diary_router
from routes.habits import router as habits_router
from routes.mood import router as mood_router
from routes.analytics import router as analytics_router
from routes.profile import router as profile_router
from routes.privacy import router as privacy_router
from routes.ai import router as ai_router
from routes.user_settings import router as user_settings_router
from routes.fitness import router as fitness_router
from routes.calendar import router as calendar_router
from routes.notion import router as notion_router
from routes.generate import router as generate_router
from routes.user import router as user_router
from routes.auth import router as auth_router
from routes.tasks import router as tasks_router
from routes.goals import router as goals_router
from routes.schedule_blocks import router as schedule_blocks_router
from routes.flashcards import router as flashcards_router
from routes.notifications import router as notifications_router

# Security middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

# Token tracking middleware
class TokenTrackingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Track token usage for AI endpoints
        if request.url.path.startswith("/api/") and any(ai_path in request.url.path for ai_path in ["/plan-day", "/generate-flashcards", "/insights"]):
            # This would be implemented to track actual token usage from OpenAI responses
            # For now, we'll just log the request
            pass
        
        return response

def create_app(redis_client=None):
    app = FastAPI(
        title="Personal Agent API",
        description="API for personal productivity and habits tracking.",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Security: Trusted Host Middleware (only allow specific hosts in production)
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=["yourdomain.com", "api.yourdomain.com", "localhost"]
        )

    # Add middleware in correct order
    app.add_middleware(SecurityHeadersMiddleware)  # Security headers first
    app.add_middleware(TokenTrackingMiddleware)  # Token tracking
    app.add_middleware(RequestContextMiddleware)  # Request context
    app.add_middleware(LoggingMiddleware)  # Logging
    
    # Configure CORS based on environment
    if os.getenv("ENVIRONMENT") == "production":
        allowed_origins = [
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            "https://app.yourdomain.com"
        ]
    else:
        allowed_origins = [
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://test",  # For test client
            "http://testserver",  # For test client
            "*"  # Allow all origins in development
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,
    )

    # Add rate limiting middleware using Redis
    redis_client = get_redis_client()
    if os.getenv("DISABLE_RATE_LIMIT") != "true" and redis_client.is_connected():
        print(f"Setting up rate limiter with Redis client")
        
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            # Get client IP or user ID for rate limiting
            client_id = request.headers.get("X-Forwarded-For", request.client.host)
            
            # Check rate limit
            rate_limit_key = f"rate_limit:{client_id}"
            if not redis_client.check_rate_limit(rate_limit_key, 60, 60):  # 60 requests per minute
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."}
                )
            
            return await call_next(request)
    else:
        print(f"Rate limiting disabled. DISABLE_RATE_LIMIT={os.getenv('DISABLE_RATE_LIMIT')}, redis_connected={redis_client.is_connected() if redis_client else False}")

    # Register error handlers
    app.add_exception_handler(APIError, error_handler)
    app.add_exception_handler(Exception, error_handler)

    # Include all routers
    app.include_router(diary_router, prefix="/api")
    app.include_router(habits_router, prefix="/api")
    app.include_router(mood_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(profile_router, prefix="/api")
    app.include_router(privacy_router, prefix="/api")
    app.include_router(ai_router, prefix="/api")
    app.include_router(user_settings_router, prefix="/api")
    app.include_router(fitness_router, prefix="/api")
    app.include_router(calendar_router, prefix="/api")
    app.include_router(notion_router, prefix="/api")
    app.include_router(generate_router, prefix="/api")
    app.include_router(user_router, prefix="/api")
    app.include_router(auth_router)
    app.include_router(tasks_router, prefix="/api")
    app.include_router(goals_router, prefix="/api")
    app.include_router(schedule_blocks_router, prefix="/api")
    app.include_router(flashcards_router, prefix="/api")
    app.include_router(notifications_router, prefix="/api")

    @app.get("/", tags=["Root"], summary="Root endpoint with meta tags for SEO")
    async def root():
        return {
            "message": "Welcome to the Personal Agent API",
            "meta": {
                "title": "Personal Agent API",
                "description": "API for personal productivity and habits tracking.",
                "keywords": "productivity, habits, tracking, API"
            }
        }

    @app.options("/", tags=["Root"], summary="CORS preflight handler")
    async def root_options():
        return {"message": "OK"}

    @app.get("/health", tags=["Health"], summary="Health check endpoint")
    async def health_check():
        redis_status = "connected" if redis_client.is_connected() else "disconnected"
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "redis": redis_status
        }

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=monitoring_service.get_metrics(), media_type="text/plain")

    return app

# Create the FastAPI app instance
app = create_app()

# Example usage
# Run the FastAPI server with: uvicorn main:app --reload 