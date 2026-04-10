"""
Alerts Router

Provides endpoints for querying compliance alerts:
- GET /api/v1/alerts/expiry - Get document expiry alerts

Returns documents that are expiring within a specified number of days.
"""

from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from app.middleware.rate_limit import limiter
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.common import PaginatedResponse
import math

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)


# Mock data for documents (to be replaced with database queries)
MOCK_DOCUMENTS = [
    Document(
        id=1,
        supplier_id=1,
        supplier_name="ABC Construction Supplies Ltd.",
        document_type=DocumentType.INSURANCE,
        document_name="General Liability Insurance Certificate",
        file_path="/uploads/documents/2024/01/insurance_cert_abc_2024.pdf",
        file_size=245678,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 1, 0, 0, 0),
        expiry_date=datetime(2026, 4, 20, 0, 0, 0),  # Expiring in 10 days
        status=DocumentStatus.EXPIRING_SOON,
        is_required=True,
        validation_notes="Verified on 2024-01-15",
        uploaded_by="admin@makyol.com",
        uploaded_at=datetime(2024, 1, 15, 10, 30, 0),
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 10, 30, 0)
    ),
    Document(
        id=2,
        supplier_id=2,
        supplier_name="XYZ Equipment Rental",
        document_type=DocumentType.TAX,
        document_name="Tax Compliance Certificate",
        file_path="/uploads/documents/2024/02/tax_cert_xyz_2024.pdf",
        file_size=189234,
        mime_type="application/pdf",
        issue_date=datetime(2024, 2, 1, 0, 0, 0),
        expiry_date=datetime(2026, 4, 25, 0, 0, 0),  # Expiring in 15 days
        status=DocumentStatus.EXPIRING_SOON,
        is_required=True,
        validation_notes="Annual tax certificate renewal",
        uploaded_by="finance@makyol.com",
        uploaded_at=datetime(2024, 2, 10, 9, 0, 0),
        created_at=datetime(2024, 2, 10, 9, 0, 0),
        updated_at=datetime(2024, 2, 10, 9, 0, 0)
    ),
    Document(
        id=3,
        supplier_id=3,
        supplier_name="Professional Engineering Consultants",
        document_type=DocumentType.QUALITY,
        document_name="ISO 9001:2015 Certificate",
        file_path="/uploads/documents/2023/11/iso_cert_proeng_2023.pdf",
        file_size=312456,
        mime_type="application/pdf",
        issue_date=datetime(2023, 11, 5, 0, 0, 0),
        expiry_date=datetime(2026, 5, 5, 0, 0, 0),  # Expiring in 25 days
        status=DocumentStatus.EXPIRING_SOON,
        is_required=True,
        validation_notes="Quality management certification",
        uploaded_by="quality@makyol.com",
        uploaded_at=datetime(2023, 11, 5, 11, 15, 0),
        created_at=datetime(2023, 11, 5, 11, 15, 0),
        updated_at=datetime(2024, 3, 10, 10, 0, 0)
    ),
    Document(
        id=4,
        supplier_id=1,
        supplier_name="ABC Construction Supplies Ltd.",
        document_type=DocumentType.LICENSE,
        document_name="Construction License",
        file_path="/uploads/documents/2024/01/license_abc_2024.pdf",
        file_size=198765,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 10, 0, 0, 0),
        expiry_date=datetime(2026, 6, 10, 0, 0, 0),  # Expiring in 61 days
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Valid construction license",
        uploaded_by="compliance@makyol.com",
        uploaded_at=datetime(2024, 1, 20, 8, 30, 0),
        created_at=datetime(2024, 1, 20, 8, 30, 0),
        updated_at=datetime(2024, 3, 25, 12, 0, 0)
    ),
    Document(
        id=5,
        supplier_id=4,
        supplier_name="Labor Solutions SRL",
        document_type=DocumentType.SAFETY,
        document_name="Workplace Safety Certificate",
        file_path="/uploads/documents/2024/02/safety_cert_labor_2024.pdf",
        file_size=234567,
        mime_type="application/pdf",
        issue_date=datetime(2024, 2, 15, 0, 0, 0),
        expiry_date=datetime(2026, 7, 15, 0, 0, 0),  # Expiring in 96 days
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Safety compliance verified",
        uploaded_by="safety@makyol.com",
        uploaded_at=datetime(2024, 2, 20, 14, 0, 0),
        created_at=datetime(2024, 2, 20, 14, 0, 0),
        updated_at=datetime(2024, 3, 1, 9, 30, 0)
    ),
    Document(
        id=6,
        supplier_id=2,
        supplier_name="XYZ Equipment Rental",
        document_type=DocumentType.INSURANCE,
        document_name="Equipment Insurance Policy",
        file_path="/uploads/documents/2024/03/insurance_xyz_2024.pdf",
        file_size=276543,
        mime_type="application/pdf",
        issue_date=datetime(2024, 3, 1, 0, 0, 0),
        expiry_date=datetime(2027, 3, 1, 0, 0, 0),  # Expiring in 325 days
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Comprehensive equipment coverage",
        uploaded_by="insurance@makyol.com",
        uploaded_at=datetime(2024, 3, 5, 10, 0, 0),
        created_at=datetime(2024, 3, 5, 10, 0, 0),
        updated_at=datetime(2024, 3, 5, 10, 0, 0)
    )
]


def filter_expiring_documents(
    documents: list[Document],
    days: int,
    document_type: Optional[DocumentType] = None,
    supplier_id: Optional[int] = None
) -> list[Document]:
    """
    Filter documents that are expiring within the specified number of days.

    Args:
        documents: List of documents to filter
        days: Number of days to check for expiry (documents expiring within this period)
        document_type: Optional filter by document type
        supplier_id: Optional filter by supplier ID

    Returns:
        Filtered list of documents expiring within the specified timeframe
    """
    # Calculate the threshold date (today + days)
    current_date = datetime.now()
    threshold_date = current_date + timedelta(days=days)

    # Filter documents by expiry date
    filtered = [
        d for d in documents
        if d.expiry_date is not None
        and current_date <= d.expiry_date <= threshold_date
    ]

    # Apply optional filters
    if document_type is not None:
        filtered = [d for d in filtered if d.document_type == document_type]

    if supplier_id is not None:
        filtered = [d for d in filtered if d.supplier_id == supplier_id]

    # Sort by expiry date (soonest first)
    filtered.sort(key=lambda d: d.expiry_date)

    return filtered


@router.get(
    "/expiry",
    response_model=PaginatedResponse[Document],
    summary="Get Document Expiry Alerts",
    description="Get documents that are expiring within a specified number of days, sorted by expiry date."
)
@limiter.limit("100/minute")
async def get_expiry_alerts(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to check for expiry (documents expiring within this period)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    supplier_id: Optional[int] = Query(None, ge=1, description="Filter by supplier ID")
):
    """
    Get documents that are expiring within a specified number of days.

    Returns documents sorted by expiry date (soonest first) with pagination support.

    **Query Parameters:**
    - **days**: Number of days to check for expiry (1-365, default: 30)
    - **page**: Page number (1-indexed, default: 1)
    - **limit**: Items per page (1-100, default: 10)
    - **document_type**: Filter by document type (insurance, tax, license, etc.)
    - **supplier_id**: Filter by supplier ID

    **Returns:**
    - Paginated list of documents expiring within the specified timeframe
    - Documents are sorted by expiry date (soonest expiry first)

    **Example:**
    ```
    GET /api/v1/alerts/expiry?days=30&page=1&limit=10
    GET /api/v1/alerts/expiry?days=7&document_type=insurance
    GET /api/v1/alerts/expiry?days=60&supplier_id=1
    ```
    """
    # Filter documents based on query parameters
    filtered_documents = filter_expiring_documents(
        MOCK_DOCUMENTS,
        days=days,
        document_type=document_type,
        supplier_id=supplier_id
    )

    # Calculate pagination
    total = len(filtered_documents)
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
    paginated_data = filtered_documents[start_idx:end_idx]

    # Build response
    return PaginatedResponse[Document](
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
