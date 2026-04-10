"""
Suppliers Router

Provides endpoints for querying supplier information:
- GET /api/v1/suppliers - List all suppliers with filtering and pagination
- GET /api/v1/suppliers/{id} - Get supplier details by ID

Supports filtering by category, active status, and text search.
"""

from fastapi import APIRouter, Request, Query, HTTPException, Path
from typing import Optional
from datetime import datetime
from app.middleware.rate_limit import limiter
from app.models.supplier import Supplier, SupplierCategory, ComplianceStatus
from app.models.common import PaginatedResponse
import math

router = APIRouter(
    prefix="/api/v1/suppliers",
    tags=["Suppliers"]
)


# Mock data for suppliers (to be replaced with database queries)
MOCK_SUPPLIERS = [
    Supplier(
        id=1,
        name="ABC Construction Supplies Ltd.",
        registration_number="CR-2023-45678",
        tax_id="TR-987654321",
        category=SupplierCategory.CONSTRUCTION,
        email="contact@abcconstruction.com",
        phone="+40-21-555-0123",
        address="123 Industrial Park, Bucharest, Romania",
        contact_person="John Popescu",
        is_active=True,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 3, 20, 14, 45, 0)
    ),
    Supplier(
        id=2,
        name="XYZ Equipment Rental",
        registration_number="CR-2024-12345",
        tax_id="TR-123456789",
        category=SupplierCategory.EQUIPMENT,
        email="info@xyzrental.com",
        phone="+40-21-555-9876",
        address="456 Business District, Cluj-Napoca, Romania",
        contact_person="Maria Ionescu",
        is_active=True,
        created_at=datetime(2024, 2, 10, 9, 0, 0),
        updated_at=datetime(2024, 3, 15, 16, 30, 0)
    ),
    Supplier(
        id=3,
        name="Professional Engineering Consultants",
        registration_number="CR-2023-98765",
        tax_id="TR-555666777",
        category=SupplierCategory.CONSULTING,
        email="contact@proeng.ro",
        phone="+40-21-555-4567",
        address="789 Tech Plaza, Timisoara, Romania",
        contact_person="Alex Gheorghe",
        is_active=True,
        created_at=datetime(2023, 11, 5, 11, 15, 0),
        updated_at=datetime(2024, 3, 10, 10, 0, 0)
    ),
    Supplier(
        id=4,
        name="Labor Solutions SRL",
        registration_number="CR-2024-11111",
        tax_id="TR-111222333",
        category=SupplierCategory.LABOR,
        email="hr@laborsolutions.ro",
        phone="+40-21-555-7890",
        address="321 Worker Street, Iasi, Romania",
        contact_person="Ana Mihai",
        is_active=True,
        created_at=datetime(2024, 1, 20, 8, 30, 0),
        updated_at=datetime(2024, 3, 25, 12, 0, 0)
    ),
    Supplier(
        id=5,
        name="Inactive Supplier Co.",
        registration_number="CR-2022-99999",
        tax_id="TR-999888777",
        category=SupplierCategory.OTHER,
        email="contact@inactive.com",
        phone="+40-21-555-0000",
        address="999 Old Road, Constanta, Romania",
        contact_person="Dan Petre",
        is_active=False,
        created_at=datetime(2022, 6, 1, 10, 0, 0),
        updated_at=datetime(2023, 12, 31, 23, 59, 59)
    )
]


def filter_suppliers(
    suppliers: list[Supplier],
    category: Optional[SupplierCategory] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> list[Supplier]:
    """
    Filter suppliers based on query parameters.

    Args:
        suppliers: List of suppliers to filter
        category: Filter by supplier category
        is_active: Filter by active status
        search: Search in supplier name, registration number, or contact person

    Returns:
        Filtered list of suppliers
    """
    filtered = suppliers

    if category is not None:
        filtered = [s for s in filtered if s.category == category]

    if is_active is not None:
        filtered = [s for s in filtered if s.is_active == is_active]

    if search:
        search_lower = search.lower()
        filtered = [
            s for s in filtered
            if (search_lower in s.name.lower() or
                (s.registration_number and search_lower in s.registration_number.lower()) or
                (s.contact_person and search_lower in s.contact_person.lower()))
        ]

    return filtered


@router.get(
    "",
    response_model=PaginatedResponse[Supplier],
    summary="List Suppliers",
    description="Get a paginated list of suppliers with optional filtering by category, active status, and search."
)
@limiter.limit("100/minute")
async def list_suppliers(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
    category: Optional[SupplierCategory] = Query(None, description="Filter by supplier category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=1, max_length=255, description="Search in name, registration number, or contact person")
):
    """
    List all suppliers with filtering and pagination.

    **Query Parameters:**
    - **page**: Page number (1-indexed, default: 1)
    - **limit**: Items per page (1-100, default: 10)
    - **category**: Filter by category (construction, equipment, consulting, labor, other)
    - **is_active**: Filter by active status (true/false)
    - **search**: Search text to match against name, registration number, or contact person

    **Returns:**
    - Paginated list of suppliers with metadata (total count, page info, navigation)

    **Example:**
    ```
    GET /api/v1/suppliers?page=1&limit=10&category=construction&is_active=true
    ```
    """
    # Filter suppliers based on query parameters
    filtered_suppliers = filter_suppliers(
        MOCK_SUPPLIERS,
        category=category,
        is_active=is_active,
        search=search
    )

    # Calculate pagination
    total = len(filtered_suppliers)
    total_pages = math.ceil(total / limit) if total > 0 else 0

    # Validate page number
    if page > total_pages and total > 0:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page} not found. Total pages: {total_pages}"
        )

    # Get paginated data
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_data = filtered_suppliers[start_idx:end_idx]

    # Build response
    return PaginatedResponse[Supplier](
        data=paginated_data,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
        next_page=page + 1 if page < total_pages else None,
        previous_page=page - 1 if page > 1 else None
    )


@router.get(
    "/{supplier_id}",
    response_model=Supplier,
    summary="Get Supplier by ID",
    description="Retrieve detailed information about a specific supplier by ID."
)
@limiter.limit("100/minute")
async def get_supplier(
    request: Request,
    supplier_id: int = Path(..., gt=0, description="Supplier ID")
):
    """
    Get detailed information about a specific supplier.

    **Path Parameters:**
    - **supplier_id**: Unique supplier identifier (must be > 0)

    **Returns:**
    - Supplier details including contact information and metadata

    **Errors:**
    - **404**: Supplier not found

    **Example:**
    ```
    GET /api/v1/suppliers/1
    ```
    """
    # Find supplier by ID
    supplier = next((s for s in MOCK_SUPPLIERS if s.id == supplier_id), None)

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with ID {supplier_id} not found"
        )

    return supplier
