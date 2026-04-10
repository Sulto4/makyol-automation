"""
Common response models

Defines generic response models used across all API endpoints.
Includes pagination support and standardized error responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime


# Generic type variable for paginated responses
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response model for list endpoints.

    Wraps any list of items with pagination metadata. Used by all
    list endpoints (suppliers, documents, alerts, etc.) to provide
    consistent pagination structure and navigation information.

    Type parameter T represents the type of items in the data list.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"},
                    {"id": 3, "name": "Item 3"}
                ],
                "total": 125,
                "page": 1,
                "page_size": 10,
                "total_pages": 13,
                "has_next": True,
                "has_previous": False,
                "next_page": 2,
                "previous_page": None
            }
        }
    )

    data: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items across all pages", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1, le=100)
    total_pages: int = Field(..., description="Total number of pages", ge=0)
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_page: Optional[int] = Field(None, description="Next page number (null if no next page)", ge=1)
    previous_page: Optional[int] = Field(None, description="Previous page number (null if no previous page)", ge=1)


class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    Provides consistent error structure across all API endpoints.
    Used by error handlers and exception middleware to format
    error responses with detailed information for debugging.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Resource not found",
                "error_code": "NOT_FOUND",
                "message": "Supplier with ID 999 does not exist",
                "details": {
                    "resource": "supplier",
                    "resource_id": 999
                },
                "path": "/api/v1/suppliers/999",
                "timestamp": "2024-04-10T14:30:00Z",
                "request_id": "req_1234567890abcdef"
            }
        }
    )

    error: str = Field(..., description="Short error description", min_length=1, max_length=255)
    error_code: str = Field(
        ...,
        description="Machine-readable error code (e.g., NOT_FOUND, VALIDATION_ERROR, UNAUTHORIZED)",
        min_length=1,
        max_length=100
    )
    message: str = Field(..., description="Detailed human-readable error message", min_length=1)
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Additional error details (e.g., validation errors, resource IDs)"
    )
    path: Optional[str] = Field(None, description="API endpoint path where error occurred", max_length=500)
    timestamp: datetime = Field(..., description="Timestamp when error occurred")
    request_id: Optional[str] = Field(
        None,
        description="Unique request identifier for tracking and debugging",
        max_length=100
    )


class SuccessResponse(BaseModel):
    """
    Standardized success response model for non-list operations.

    Used for operations that don't return a specific data model
    (e.g., delete operations, bulk operations, status updates).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "affected_records": 5,
                    "operation": "bulk_update"
                },
                "timestamp": "2024-04-10T14:30:00Z"
            }
        }
    )

    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Success message", min_length=1, max_length=500)
    data: Optional[dict[str, Any]] = Field(None, description="Optional additional data about the operation")
    timestamp: datetime = Field(..., description="Timestamp when operation completed")


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    Used by the /health endpoint to report API status and availability.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-04-10T14:30:00Z",
                "uptime_seconds": 86400,
                "services": {
                    "database": "healthy",
                    "storage": "healthy"
                }
            }
        }
    )

    status: str = Field(..., description="Overall system status (healthy, degraded, unhealthy)", max_length=50)
    version: str = Field(..., description="API version", max_length=50)
    timestamp: datetime = Field(..., description="Current server timestamp")
    uptime_seconds: Optional[int] = Field(None, description="Server uptime in seconds", ge=0)
    services: Optional[dict[str, str]] = Field(
        None,
        description="Status of dependent services (database, storage, etc.)"
    )
