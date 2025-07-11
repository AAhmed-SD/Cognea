"""
Main FastAPI Application with Enhanced Features
- Enhanced Redis caching
- Background workers
- Performance monitoring
- Health checks
- Metrics endpoints
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from middleware.error_handler import setup_error_handlers
from middleware.logging import setup_logging
from middleware.rate_limit import setup_rate_limiting

# Import routes
from routes import (
    ai,
    analytics,
    auth,
    calendar,
    diary,
    fitness,
    flashcards,
    generate,
    goals,
    habits,
    mood,
    notifications,
    notion,
    privacy,
    profile,
    schedule_blocks,
    stripe,
    tasks,
    user,
    user_settings,
)
# Optional exam papers feature - only import if available
try:
    from routes.exam_papers import router as exam_papers_router
    EXAM_PAPERS_ENABLED = True
except ImportError as e:
    logger.warning(f"Exam papers feature disabled: {e}")
    EXAM_PAPERS_ENABLED = False
    exam_papers_router = None
from services.background_workers import background_worker, job_scheduler
from services.performance_monitor import get_performance_monitor

# Import enhanced services
from services.redis_cache import enhanced_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for Cognie AI Personal Assistant.

    This function handles the startup and shutdown of all application services
    including Redis cache, background workers, job scheduler, and performance monitoring.

    Args:
        app (FastAPI): The FastAPI application instance

    Yields:
        None: Control is yielded to the application runtime

    Raises:
        Exception: If any service fails to start, the application will fail to start
    """
    # Startup phase - Initialize all core services
    logger.info("Starting Cognie AI Personal Assistant...")

    try:
        # Initialize Redis cache with health monitoring
        # This provides fast data access and session storage
        await enhanced_cache.start_health_check()
        logger.info("Enhanced Redis cache started")

        # Start background workers for async task processing
        # Handles AI operations, email sending, and data processing
        await background_worker.start()
        logger.info("Background workers started")

        # Initialize job scheduler for recurring tasks
        # Manages scheduled operations like daily briefs and reminders
        await job_scheduler.start()
        logger.info("Job scheduler started")

        # Start performance monitoring system
        # Tracks system metrics, response times, and generates alerts
        await get_performance_monitor().start()
        logger.info("Performance monitoring started")

        # Configure alert thresholds for different system metrics
        # These thresholds trigger warnings and critical alerts
        performance_monitor = get_performance_monitor()
        performance_monitor.alert_thresholds = {
            "cpu_usage": {"warning": 80, "critical": 95},  # CPU utilization limits
            "memory_usage": {"warning": 85, "critical": 95},  # Memory usage limits
            "disk_usage": {"warning": 90, "critical": 95},  # Disk space limits
            "error_rate": {"warning": 5, "critical": 10},  # Error percentage limits
            "avg_response_time": {
                "warning": 1.0,
                "critical": 2.0,
            },  # Response time limits
        }

        # Set up alert handler for performance notifications
        # Logs alerts and can be extended to send notifications
        def alert_handler(alert):
            logger.warning(
                f"Performance Alert: {alert.severity.upper()} - {alert.message}"
            )

        performance_monitor.add_alert_handler(alert_handler)

        logger.info("Cognie AI Personal Assistant started successfully!")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    # Application runtime - yield control to FastAPI
    yield

    # Shutdown phase - Gracefully stop all services
    logger.info("Shutting down Cognie AI Personal Assistant...")

    try:
        # Stop performance monitoring first to prevent new metrics
        await get_performance_monitor().stop()
        logger.info("Performance monitoring stopped")

        # Stop job scheduler to prevent new scheduled tasks
        await job_scheduler.stop()
        logger.info("Job scheduler stopped")

        # Stop background workers and wait for current tasks to complete
        await background_worker.stop()
        logger.info("Background workers stopped")

        # Close Redis connections and flush any pending data
        await enhanced_cache.close()
        logger.info("Enhanced Redis cache stopped")

        logger.info("Cognie AI Personal Assistant stopped successfully!")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Cognie AI Personal Assistant",
    description="An intelligent personal productivity assistant with AI integration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


def create_app():
    """Create and return the FastAPI application instance for testing."""
    return app


# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup custom middleware
setup_error_handlers(app)
setup_logging(app)
setup_rate_limiting(app)


# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """
    Middleware to monitor request performance and add performance headers.

    This middleware tracks request duration, status codes, and adds performance
    headers to responses for monitoring and debugging purposes.

    Args:
        request (Request): The incoming HTTP request
        call_next: The next middleware or route handler in the chain

    Returns:
        Response: The HTTP response with performance headers added
    """
    # Record start time for performance measurement
    start_time = time.time()

    # Process the request through the middleware chain
    response = await call_next(request)

    # Calculate request duration in seconds
    duration = time.time() - start_time

    # Record request metrics for monitoring and analytics
    # This data is used for performance analysis and alerting
    await get_performance_monitor().record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )

    # Add performance headers for client-side monitoring
    # X-Response-Time: Request duration for debugging
    # X-Request-ID: Unique identifier for request tracing
    response.headers["X-Response-Time"] = str(duration)
    response.headers["X-Request-ID"] = str(time.time())

    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring system status.

    This endpoint checks the health of all critical services including
    Redis cache, background workers, and performance monitoring.

    Returns:
        dict: Health status with service status and system metrics

    Example Response:
        {
            "status": "healthy",
            "timestamp": 1640995200.0,
            "services": {
                "redis_cache": "healthy",
                "background_workers": "healthy",
                "performance_monitor": "healthy"
            },
            "system_metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 23.1
            }
        }
    """
    try:
        # Check Redis cache connectivity and health
        # Redis is critical for session storage and caching
        redis_healthy = enhanced_cache.client is not None

        # Verify background workers are running
        # Background workers handle async tasks and AI operations
        worker_healthy = background_worker.running

        # Check performance monitoring system
        # Performance monitoring tracks system health and metrics
        monitor_healthy = get_performance_monitor().running

        # Collect current system performance metrics
        # These metrics help identify performance issues
        system_metrics = get_performance_monitor().get_performance_summary()

        # Determine overall health status
        # System is healthy only if all critical services are running
        health_status = {
            "status": (
                "healthy"
                if all([redis_healthy, worker_healthy, monitor_healthy])
                else "unhealthy"
            ),
            "timestamp": time.time(),
            "services": {
                "redis_cache": "healthy" if redis_healthy else "unhealthy",
                "background_workers": "healthy" if worker_healthy else "unhealthy",
                "performance_monitor": "healthy" if monitor_healthy else "unhealthy",
            },
            "system_metrics": system_metrics,
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    try:
        # Get recent metrics
        recent_metrics = await get_performance_monitor().get_metrics(limit=100)

        # Get worker metrics
        worker_metrics = background_worker.get_metrics()

        # Get cache metrics
        cache_metrics = enhanced_cache.get_metrics()

        # Get optimization recommendations
        recommendations = (
            await get_performance_monitor().get_optimization_recommendations()
        )

        return {
            "performance_metrics": recent_metrics,
            "worker_metrics": worker_metrics,
            "cache_metrics": cache_metrics,
            "optimization_recommendations": recommendations,
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}


# Alerts endpoint
@app.get("/alerts")
async def get_alerts(resolved: bool = None, limit: int = 50):
    """Get performance alerts"""
    try:
        alerts = await get_performance_monitor().get_alerts(
            resolved=resolved, limit=limit
        )
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return {"error": str(e)}


# Cache management endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        return enhanced_cache.get_metrics()
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


@app.post("/cache/clear")
async def clear_cache(pattern: str = "*"):
    """Clear cache entries"""
    try:
        deleted = await enhanced_cache.clear_pattern(pattern)
        return {"deleted_entries": deleted, "pattern": pattern}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {"error": str(e)}


# Background task management endpoints
@app.get("/tasks/status/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    try:
        task = await background_worker.get_task_status(task_id)
        if task:
            return task.to_dict()
        return {"error": "Task not found"}
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {"error": str(e)}


@app.post("/tasks/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a background task"""
    try:
        cancelled = await background_worker.cancel_task(task_id)
        return {"cancelled": cancelled, "task_id": task_id}
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return {"error": str(e)}


# Include all route modules
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/user", tags=["User Management"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(habits.router, prefix="/api/habits", tags=["Habits"])
app.include_router(schedule_blocks.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["Flashcards"])
app.include_router(
    notifications.router, prefix="/api/notifications", tags=["Notifications"]
)
app.include_router(ai.router, prefix="/api/ai", tags=["AI Services"])
app.include_router(generate.router, prefix="/api/generate", tags=["Content Generation"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(mood.router, prefix="/api/mood", tags=["Mood Tracking"])
app.include_router(notion.router, prefix="/api/notion", tags=["Notion Integration"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["Payment"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(user_settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(privacy.router, prefix="/api/privacy", tags=["Privacy"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(diary.router, prefix="/api/diary", tags=["Diary"])
app.include_router(fitness.router, prefix="/api/fitness", tags=["Fitness"])
# Include exam papers router only if enabled
if EXAM_PAPERS_ENABLED and exam_papers_router:
    app.include_router(exam_papers_router, prefix="/api/exam-papers", tags=["Exam Papers"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Cognie AI Personal Assistant API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Enhanced Redis Caching",
            "Background Workers",
            "Performance Monitoring",
            "AI Integration",
            "Notion Sync",
            "Stripe Payments",
            "Real-time Analytics",
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "alerts": "/alerts",
        },
        "meta": {
            "timestamp": time.time(),
            "environment": os.getenv("ENVIRONMENT", "development"),
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
