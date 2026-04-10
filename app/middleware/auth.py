"""
Authentication Middleware

Middleware for validating API key authentication via X-API-Key header.
Protects all /api/v1/* endpoints while allowing public access to docs and health checks.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.api_keys import validate_api_key


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication on API endpoints.

    Checks for X-API-Key header on all /api/v1/* routes.
    Returns 401 Unauthorized if the key is missing or invalid.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        """
        Process each request and validate API key for protected endpoints.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: Either an error response or the result from call_next
        """
        # Allow public paths without authentication
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if this is an API endpoint that requires authentication
        if request.url.path.startswith("/api/v1/"):
            # Extract API key from X-API-Key header
            api_key = request.headers.get("X-API-Key")

            # Validate the API key
            if not validate_api_key(api_key):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid or missing API key",
                        "error": "Unauthorized",
                        "message": "Please provide a valid API key in the X-API-Key header"
                    }
                )

        # API key is valid or path doesn't require auth, continue
        response = await call_next(request)
        return response
