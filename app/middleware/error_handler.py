"""
Error Handling Middleware

Provides consistent error handling across all API endpoints.
Catches common HTTP exceptions and returns standardized JSON error responses.
"""

import uuid
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for HTTP exceptions (404, 403, etc.).

    Converts standard HTTP exceptions into consistent JSON error responses
    with error codes, messages, and tracking information.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSONResponse: Standardized error response
    """
    error_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
        status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }

    error_code = error_code_map.get(exc.status_code, "UNKNOWN_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "error_code": error_code,
            "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "details": None,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4())
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation errors (422).

    Formats Pydantic validation errors into a consistent structure
    with detailed information about which fields failed validation.

    Args:
        request: The incoming request
        exc: The validation error

    Returns:
        JSONResponse: Standardized validation error response
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed. Please check the request parameters and body.",
            "details": {
                "validation_errors": errors
            },
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4())
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions (500).

    Catches any exceptions that weren't handled by other handlers
    and returns a generic error response. In production, detailed
    error messages should be logged but not exposed to clients.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSONResponse: Generic internal server error response
    """
    # In production, log the full exception details
    # but only return a generic message to the client
    error_message = "An internal server error occurred. Please try again later."

    # In development/debug mode, include more details
    from app.config import settings
    if settings.debug:
        error_message = f"Internal server error: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": error_message,
            "details": None,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4())
        }
    )
