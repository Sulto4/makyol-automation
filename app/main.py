"""
Main FastAPI application module

Initializes the FastAPI application with:
- Basic configuration
- Health check endpoint
- CORS middleware
- API key authentication
- Rate limiting (100 requests/minute)
- API metadata
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.middleware.auth import APIKeyAuthMiddleware
from app.middleware.rate_limit import limiter, _rate_limit_exceeded_handler
from app.routers import test


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for querying Makyol compliance data. "
                "Supports supplier compliance status, document inventory, expiry alerts, and compliance reports.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure API Key Authentication
app.add_middleware(APIKeyAuthMiddleware)

# Include routers
app.include_router(test.router)


@app.get("/health", tags=["System"], summary="Health Check")
async def health_check():
    """
    Health check endpoint to verify API is running.

    Returns:
        dict: Health status with service name, version, and status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/", tags=["System"], summary="API Root")
async def root():
    """
    API root endpoint with basic information.

    Returns:
        dict: Welcome message and links to documentation
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }
