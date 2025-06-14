import logging.config
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime

from middleware.error_handler import error_handler, APIError
from middleware.logging import LoggingMiddleware, RequestContextMiddleware

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

def create_app():
    app = FastAPI(
        title="Personal Agent API",
        description="API for personal productivity and habits tracking.",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address)

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

    # Add rate limiting middleware if not disabled
    if os.getenv("DISABLE_RATE_LIMIT") != "true":
        app.state.limiter = limiter
        app.add_middleware(limiter.middleware)

    # Register error handlers
    app.add_exception_handler(APIError, error_handler)
    app.add_exception_handler(RateLimitExceeded, error_handler)
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