import logging.config
import os

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up structured logging
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/ai_usage.log',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

logging.config.dictConfig(logging_config)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    app = FastAPI(title="Personal Agent API", description="API for personal productivity and habits tracking.")
    limiter = Limiter(key_func=get_remote_address)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Conditionally add rate limiting middleware
    if os.getenv("DISABLE_RATE_LIMIT") != "true":
        app.state.limiter = limiter
        app.add_middleware(limiter.middleware)

    # Include all routers
    app.include_router(diary_router)
    app.include_router(habits_router)
    app.include_router(mood_router)
    app.include_router(analytics_router)
    app.include_router(profile_router)
    app.include_router(privacy_router)
    app.include_router(ai_router)
    app.include_router(user_settings_router)
    app.include_router(fitness_router)
    app.include_router(calendar_router)
    app.include_router(notion_router)
    app.include_router(generate_router)
    app.include_router(user_router)

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

    return app

app = create_app()

# Example usage
# Run the FastAPI server with: uvicorn main:app --reload 