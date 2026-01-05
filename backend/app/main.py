"""
SmartRecon-AI Backend Application
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import logging
import time

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.core.exceptions import (
    SmartReconException,
    AuthorizationError,
    ScopeValidationError,
    ToolExecutionError,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting SmartRecon-AI application...")
    
    # Create database tables
    # Note: In production, use Alembic migrations instead
    # Base.metadata.create_all(bind=engine)
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down SmartRecon-AI application...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI-assisted bug bounty reconnaissance agent",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to track request duration"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(SmartReconException)
async def smartrecon_exception_handler(request: Request, exc: SmartReconException):
    """Handle custom SmartRecon exceptions"""
    logger.error(f"SmartRecon error: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors"""
    logger.warning(f"Authorization error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "AUTHORIZATION_ERROR",
            "message": exc.message,
        },
    )


@app.exception_handler(ScopeValidationError)
async def scope_validation_error_handler(request: Request, exc: ScopeValidationError):
    """Handle scope validation errors"""
    logger.warning(f"Scope validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "SCOPE_VALIDATION_ERROR",
            "message": exc.message,
            "invalid_items": exc.details.get("invalid_items", []),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please contact support.",
        },
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "smartrecon-api",
        "version": settings.VERSION,
    }


# Readiness check endpoint
@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check for Kubernetes/orchestration"""
    # TODO: Add actual checks for database, redis, etc.
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "celery": "ok",
        }
    }


# Metrics endpoint for Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SmartRecon-AI API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
        "disclaimer": "FOR AUTHORIZED TESTING ONLY - This tool is intended for authorized security testing and bug bounty programs only.",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
