"""
Test Router

Simple test endpoint for verifying API authentication and functionality.
This router is for testing purposes only.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["Test"]
)


@router.get("/test", summary="Test Endpoint")
async def test_endpoint():
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
