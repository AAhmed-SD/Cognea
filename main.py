import logging.config
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from middleware.error_handler import error_handler, APIError
from middleware.logging import LoggingMiddleware, RequestContextMiddleware
from middleware.rate_limit import RateLimiter

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

def create_app(redis_client=None):
    app = FastAPI(
        title="Personal Agent API",
        description="API for personal productivity and habits tracking.",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Add middleware in correct order
    app.add_middleware(RequestContextMiddleware)  # First to add request context
    app.add_middleware(LoggingMiddleware)  # Then logging
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware if not disabled and Redis client is provided
    if os.getenv("DISABLE_RATE_LIMIT") != "true" and redis_client is not None:
        print(f"Setting up rate limiter with Redis client: {redis_client}")
        rate_limiter = RateLimiter(redis_client, requests_per_minute=10)
        
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            print(f"Rate limit middleware called for {request.url}")
            await rate_limiter.check_rate_limit(request)
            return await call_next(request)
    else:
        print(f"Rate limiting disabled. DISABLE_RATE_LIMIT={os.getenv('DISABLE_RATE_LIMIT')}, redis_client={redis_client is not None}")

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

    @app.get("/health", tags=["Health"], summary="Health check endpoint")
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }

    return app

app = create_app()

# Example usage
# Run the FastAPI server with: uvicorn main:app --reload 