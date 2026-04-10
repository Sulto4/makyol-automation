"""
Documents Router

Provides endpoints for querying document information:
- GET /api/v1/documents - List all documents with filtering and pagination
- GET /api/v1/documents/{id} - Get document details by ID

Supports filtering by supplier, document type, status, and text search.
"""

from fastapi import APIRouter, Request, Query, HTTPException, Path
from typing import Optional
from datetime import datetime
from app.middleware.rate_limit import limiter
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.common import PaginatedResponse
import math

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
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
        expiry_date=datetime(2025, 1, 1, 0, 0, 0),
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Verified on 2024-01-15",
        uploaded_by="admin@makyol.com",
        uploaded_at=datetime(2024, 1, 15, 10, 30, 0),
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 10, 30, 0)
    ),
    Document(
        id=2,
        supplier_id=1,
        supplier_name="ABC Construction Supplies Ltd.",
        document_type=DocumentType.TAX,
        document_name="Tax Compliance Certificate 2024",
        file_path="/uploads/documents/2024/01/tax_cert_abc_2024.pdf",
        file_size=189234,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 10, 0, 0, 0),
        expiry_date=datetime(2024, 12, 31, 0, 0, 0),
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Annual tax certificate",
        uploaded_by="admin@makyol.com",
        uploaded_at=datetime(2024, 1, 20, 9, 15, 0),
        created_at=datetime(2024, 1, 20, 9, 15, 0),
        updated_at=datetime(2024, 1, 20, 9, 15, 0)
    ),
    Document(
        id=3,
        supplier_id=2,
        supplier_name="XYZ Equipment Rental",
        document_type=DocumentType.REGISTRATION,
        document_name="Company Registration Certificate",
        file_path="/uploads/documents/2024/02/registration_xyz_2024.pdf",
        file_size=156789,
        mime_type="application/pdf",
        issue_date=datetime(2024, 2, 1, 0, 0, 0),
        expiry_date=None,
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Valid company registration",
        uploaded_by="procurement@makyol.com",
        uploaded_at=datetime(2024, 2, 10, 14, 0, 0),
        created_at=datetime(2024, 2, 10, 14, 0, 0),
        updated_at=datetime(2024, 2, 10, 14, 0, 0)
    ),
    Document(
        id=4,
        supplier_id=2,
        supplier_name="XYZ Equipment Rental",
        document_type=DocumentType.INSURANCE,
        document_name="Equipment Insurance Policy",
        file_path="/uploads/documents/2024/02/insurance_xyz_2024.pdf",
        file_size=312456,
        mime_type="application/pdf",
        issue_date=datetime(2024, 2, 15, 0, 0, 0),
        expiry_date=datetime(2024, 5, 15, 0, 0, 0),
        status=DocumentStatus.EXPIRING_SOON,
        is_required=True,
        validation_notes="Expires in April - renewal needed",
        uploaded_by="procurement@makyol.com",
        uploaded_at=datetime(2024, 2, 20, 11, 30, 0),
        created_at=datetime(2024, 2, 20, 11, 30, 0),
        updated_at=datetime(2024, 3, 25, 16, 0, 0)
    ),
    Document(
        id=5,
        supplier_id=3,
        supplier_name="Professional Engineering Consultants",
        document_type=DocumentType.QUALITY,
        document_name="ISO 9001:2015 Certificate",
        file_path="/uploads/documents/2023/11/iso_cert_proeng_2023.pdf",
        file_size=198765,
        mime_type="application/pdf",
        issue_date=datetime(2023, 11, 1, 0, 0, 0),
        expiry_date=datetime(2026, 11, 1, 0, 0, 0),
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="ISO certification verified",
        uploaded_by="quality@makyol.com",
        uploaded_at=datetime(2023, 11, 5, 15, 45, 0),
        created_at=datetime(2023, 11, 5, 15, 45, 0),
        updated_at=datetime(2023, 11, 5, 15, 45, 0)
    ),
    Document(
        id=6,
        supplier_id=3,
        supplier_name="Professional Engineering Consultants",
        document_type=DocumentType.LICENSE,
        document_name="Professional Engineering License",
        file_path="/uploads/documents/2024/01/license_proeng_2024.pdf",
        file_size=134567,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 5, 0, 0, 0),
        expiry_date=datetime(2025, 1, 5, 0, 0, 0),
        status=DocumentStatus.VALID,
        is_required=True,
        validation_notes="Current professional license",
        uploaded_by="quality@makyol.com",
        uploaded_at=datetime(2024, 1, 10, 10, 0, 0),
        created_at=datetime(2024, 1, 10, 10, 0, 0),
        updated_at=datetime(2024, 1, 10, 10, 0, 0)
    ),
    Document(
        id=7,
        supplier_id=4,
        supplier_name="Labor Solutions SRL",
        document_type=DocumentType.SAFETY,
        document_name="Workplace Safety Compliance Certificate",
        file_path="/uploads/documents/2024/01/safety_labor_2024.pdf",
        file_size=223456,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 15, 0, 0, 0),
        expiry_date=datetime(2023, 12, 31, 0, 0, 0),
        status=DocumentStatus.EXPIRED,
        is_required=True,
        validation_notes="EXPIRED - Renewal required immediately",
        uploaded_by="safety@makyol.com",
        uploaded_at=datetime(2024, 1, 20, 13, 0, 0),
        created_at=datetime(2024, 1, 20, 13, 0, 0),
        updated_at=datetime(2024, 3, 20, 14, 0, 0)
    ),
    Document(
        id=8,
        supplier_id=4,
        supplier_name="Labor Solutions SRL",
        document_type=DocumentType.CONTRACT,
        document_name="Framework Agreement 2024-2026",
        file_path="/uploads/documents/2024/01/contract_labor_2024.pdf",
        file_size=456789,
        mime_type="application/pdf",
        issue_date=datetime(2024, 1, 1, 0, 0, 0),
        expiry_date=datetime(2026, 12, 31, 0, 0, 0),
        status=DocumentStatus.VALID,
        is_required=False,
        validation_notes="Multi-year framework contract",
        uploaded_by="procurement@makyol.com",
        uploaded_at=datetime(2024, 1, 25, 9, 30, 0),
        created_at=datetime(2024, 1, 25, 9, 30, 0),
        updated_at=datetime(2024, 1, 25, 9, 30, 0)
    ),
    Document(
        id=9,
        supplier_id=1,
        supplier_name="ABC Construction Supplies Ltd.",
        document_type=DocumentType.FINANCIAL,
        document_name="Annual Financial Statement 2023",
        file_path="/uploads/documents/2024/03/financial_abc_2023.pdf",
        file_size=567890,
        mime_type="application/pdf",
        issue_date=datetime(2024, 3, 1, 0, 0, 0),
        expiry_date=None,
        status=DocumentStatus.PENDING_REVIEW,
        is_required=False,
        validation_notes="Awaiting finance team review",
        uploaded_by="finance@makyol.com",
        uploaded_at=datetime(2024, 3, 15, 11, 0, 0),
        created_at=datetime(2024, 3, 15, 11, 0, 0),
        updated_at=datetime(2024, 3, 15, 11, 0, 0)
    ),
    Document(
        id=10,
        supplier_id=5,
        supplier_name="Inactive Supplier Co.",
        document_type=DocumentType.OTHER,
        document_name="Miscellaneous Documentation",
        file_path="/uploads/documents/2022/06/misc_inactive_2022.pdf",
        file_size=98765,
        mime_type="application/pdf",
        issue_date=datetime(2022, 6, 1, 0, 0, 0),
        expiry_date=datetime(2023, 6, 1, 0, 0, 0),
        status=DocumentStatus.ARCHIVED,
        is_required=False,
        validation_notes="Archived - supplier inactive",
        uploaded_by="admin@makyol.com",
        uploaded_at=datetime(2022, 6, 5, 10, 0, 0),
        created_at=datetime(2022, 6, 5, 10, 0, 0),
        updated_at=datetime(2023, 12, 31, 23, 59, 59)
    )
]


def filter_documents(
    documents: list[Document],
    supplier_id: Optional[int] = None,
    document_type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    is_required: Optional[bool] = None,
    search: Optional[str] = None
) -> list[Document]:
    """
    Filter documents based on query parameters.

    Args:
        documents: List of documents to filter
        supplier_id: Filter by supplier ID
        document_type: Filter by document type
        status: Filter by document status
        is_required: Filter by required status
        search: Search in document name, supplier name, or validation notes

    Returns:
        Filtered list of documents
    """
    filtered = documents

    if supplier_id is not None:
        filtered = [d for d in filtered if d.supplier_id == supplier_id]

    if document_type is not None:
        filtered = [d for d in filtered if d.document_type == document_type]

    if status is not None:
        filtered = [d for d in filtered if d.status == status]

    if is_required is not None:
        filtered = [d for d in filtered if d.is_required == is_required]

    if search:
        search_lower = search.lower()
        filtered = [
            d for d in filtered
            if (search_lower in d.document_name.lower() or
                search_lower in d.supplier_name.lower() or
                (d.validation_notes and search_lower in d.validation_notes.lower()))
        ]

    return filtered


@router.get(
    "",
    response_model=PaginatedResponse[Document],
    summary="List Documents",
    description="Get a paginated list of documents with optional filtering by supplier, type, status, and search."
)
@limiter.limit("100/minute")
async def list_documents(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
    supplier_id: Optional[int] = Query(None, gt=0, description="Filter by supplier ID"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by document status"),
    is_required: Optional[bool] = Query(None, description="Filter by required status"),
    search: Optional[str] = Query(None, min_length=1, max_length=255, description="Search in document name, supplier name, or validation notes")
):
    """
    List all documents with filtering and pagination.

    **Query Parameters:**
    - **page**: Page number (1-indexed, default: 1)
    - **limit**: Items per page (1-100, default: 10)
    - **supplier_id**: Filter by supplier ID
    - **document_type**: Filter by type (registration, tax, insurance, license, financial, quality, safety, contract, other)
    - **status**: Filter by status (valid, expired, expiring_soon, pending_review, rejected, archived)
    - **is_required**: Filter by required status (true/false)
    - **search**: Search text to match against document name, supplier name, or validation notes

    **Returns:**
    - Paginated list of documents with metadata (total count, page info, navigation)

    **Example:**
    ```
    GET /api/v1/documents?page=1&limit=10&supplier_id=1&status=valid
    ```
    """
    # Filter documents based on query parameters
    filtered_documents = filter_documents(
        MOCK_DOCUMENTS,
        supplier_id=supplier_id,
        document_type=document_type,
        status=status,
        is_required=is_required,
        search=search
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


@router.get(
    "/{document_id}",
    response_model=Document,
    summary="Get Document by ID",
    description="Retrieve detailed information for a specific document by ID."
)
@limiter.limit("100/minute")
async def get_document(
    request: Request,
    document_id: int = Path(..., gt=0, description="Document ID to retrieve")
):
    """
    Get detailed information for a specific document.

    **Path Parameters:**
    - **document_id**: Unique document identifier (positive integer)

    **Returns:**
    - Document details including metadata, supplier info, file info, and validity dates

    **Example:**
    ```
    GET /api/v1/documents/1
    ```
    """
    # Find document by ID
    document = next((d for d in MOCK_DOCUMENTS if d.id == document_id), None)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )

    return document
