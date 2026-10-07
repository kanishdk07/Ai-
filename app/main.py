"""
FastAPI Main Application
Highway Accident Detection and Emergency Alert System Backend
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, close_db
from app.api.v1 import api_router
from app.api.v1.websocket import router as websocket_router
from app.services.scheduler_service import get_scheduler
from app.utils.logging import setup_logging
import logging
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Test mode: {settings.TEST_MODE}")
    logger.info(f"Maintenance mode: {settings.MAINTENANCE_MODE}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Start scheduler for notification management
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Notification scheduler started")

    # Log configuration
    logger.info(f"Auto-notification enabled: {settings.AUTO_NOTIFICATION_ENABLED}")
    logger.info(f"Notification interval: {settings.NOTIFICATION_INTERVAL_SECONDS}s")
    logger.info(f"Hospital search radius: {settings.HOSPITAL_SEARCH_RADIUS_KM}km")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Stop scheduler
    scheduler.shutdown()
    logger.info("Scheduler stopped")

    # Close database connections
    await close_db()
    logger.info("Database connections closed")

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Based Highway Accident Detection and Emergency Alert System Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket route separately (not versioned in prefix)
app.include_router(websocket_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/api/v1/admin/health",
    }


# Health check endpoint (simple)
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
