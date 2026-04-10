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
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.middleware.auth import APIKeyAuthMiddleware
from app.middleware.rate_limit import limiter, _rate_limit_exceeded_handler
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.routers import test, suppliers, compliance, documents, alerts, reports


# Initialize FastAPI app with comprehensive OpenAPI documentation
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Makyol Compliance API

REST API for querying supplier compliance data and integrating with external systems.

### Features
- 🔐 **Secure Access**: API key authentication on all endpoints
- ⚡ **Rate Limited**: 100 requests/minute to prevent abuse
- 📊 **Rich Data**: Comprehensive compliance, supplier, and document information
- 🔍 **Flexible Querying**: Filtering, pagination, and search capabilities
- 📝 **Well Documented**: OpenAPI/Swagger specification with examples

### Use Cases
- **ERP Integration**: Check supplier compliance before generating purchase orders
- **Procurement Automation**: Automate supplier verification workflows
- **Project Management**: Display compliance status in project dashboards
- **Reporting & Analytics**: Extract compliance data for business intelligence tools

### Authentication
All API endpoints (except `/health` and `/`) require authentication using an API key.
Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Rate Limiting
API requests are limited to **100 requests per minute** per API key.
Exceeding this limit will result in a `429 Too Many Requests` response.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Makyol IT Department",
        "email": "it@makyol.com",
        "url": "https://makyol.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://makyol.com/license"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local Development Server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development Environment"
        }
    ],
    openapi_tags=[
        {
            "name": "System",
            "description": "System health and API information endpoints"
        },
        {
            "name": "Test",
            "description": "Test endpoints for API key validation and connectivity checks"
        },
        {
            "name": "Suppliers",
            "description": "Query and filter supplier information. Supports pagination and search by name, category, or registration number."
        },
        {
            "name": "Compliance",
            "description": "Retrieve supplier compliance status including audit dates, document counts, and compliance scores."
        },
        {
            "name": "Documents",
            "description": "Access document inventory with filtering by supplier, type, status, and expiry dates."
        },
        {
            "name": "Alerts",
            "description": "Get proactive alerts for expiring documents and compliance issues."
        },
        {
            "name": "Reports",
            "description": "Generate comprehensive compliance reports with statistics and insights. Supports multiple output formats."
        }
    ]
)

# Configure Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure Error Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

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
app.include_router(suppliers.router)
app.include_router(compliance.router)
app.include_router(documents.router)
app.include_router(alerts.router)
app.include_router(reports.router)


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
