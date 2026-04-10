"""
Rate Limiting Middleware

Implements rate limiting using SlowAPI to prevent API abuse.
Default limit: 100 requests per minute per client IP.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.config import settings


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a consistent JSON error response when rate limit is exceeded.

    Args:
        request: The incoming request
        exc: The RateLimitExceeded exception

    Returns:
        JSONResponse: 429 Too Many Requests with error details
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "error": "Too Many Requests",
            "message": f"You have exceeded the rate limit. Please try again later.",
            "retry_after": str(exc.detail).split("Retry after ")[1] if "Retry after" in str(exc.detail) else None
        }
    )


# Initialize limiter with configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)
