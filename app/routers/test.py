"""
Test Router

Simple test endpoint for verifying API authentication and functionality.
This router is for testing purposes only.
"""

from fastapi import APIRouter, Request
from app.middleware.rate_limit import limiter

router = APIRouter(
    prefix="/api/v1",
    tags=["Test"]
)


@router.get("/test", summary="Test Endpoint")
@limiter.limit(f"100/minute")
async def test_endpoint(request: Request):
    """
    Test endpoint to verify API is working and authentication is enabled.

    Returns:
        dict: Simple test response
    """
    return {
        "status": "success",
        "message": "API is working correctly",
        "authenticated": True
    }
