"""
Compliance Router

Provides endpoints for querying supplier compliance status:
- GET /api/v1/compliance/suppliers/{id} - Get compliance status for a specific supplier

Returns detailed compliance information including document counts, audit dates,
and overall compliance status.
"""

from fastapi import APIRouter, Request, HTTPException, Path
from datetime import datetime
from app.middleware.rate_limit import limiter
from app.models.supplier import SupplierCompliance, ComplianceStatus

router = APIRouter(
    prefix="/api/v1/compliance",
    tags=["Compliance"]
)


# Mock data for supplier compliance (to be replaced with database queries)
MOCK_COMPLIANCE_DATA = [
    SupplierCompliance(
        supplier_id=1,
        supplier_name="ABC Construction Supplies Ltd.",
        compliance_status=ComplianceStatus.COMPLIANT,
        last_audit_date=datetime(2024, 2, 15, 10, 0, 0),
        next_audit_date=datetime(2024, 8, 15, 10, 0, 0),
        total_documents=12,
        valid_documents=11,
        expired_documents=0,
        expiring_soon_documents=1,
        missing_required_documents=0,
        compliance_score=95.5,
        notes="Annual audit completed. One document expiring in 30 days.",
        last_checked_at=datetime(2024, 3, 20, 14, 45, 0)
    ),
    SupplierCompliance(
        supplier_id=2,
        supplier_name="XYZ Equipment Rental",
        compliance_status=ComplianceStatus.COMPLIANT,
        last_audit_date=datetime(2024, 3, 1, 9, 30, 0),
        next_audit_date=datetime(2024, 9, 1, 9, 30, 0),
        total_documents=8,
        valid_documents=8,
        expired_documents=0,
        expiring_soon_documents=0,
        missing_required_documents=0,
        compliance_score=100.0,
        notes="All documents valid. No issues found.",
        last_checked_at=datetime(2024, 3, 25, 16, 30, 0)
    ),
    SupplierCompliance(
        supplier_id=3,
        supplier_name="Professional Engineering Consultants",
        compliance_status=ComplianceStatus.NON_COMPLIANT,
        last_audit_date=datetime(2024, 1, 10, 14, 0, 0),
        next_audit_date=datetime(2024, 7, 10, 14, 0, 0),
        total_documents=10,
        valid_documents=7,
        expired_documents=2,
        expiring_soon_documents=1,
        missing_required_documents=1,
        compliance_score=65.0,
        notes="Missing professional liability insurance. Two certificates expired.",
        last_checked_at=datetime(2024, 3, 22, 10, 15, 0)
    ),
    SupplierCompliance(
        supplier_id=4,
        supplier_name="Labor Solutions SRL",
        compliance_status=ComplianceStatus.PENDING,
        last_audit_date=datetime(2024, 3, 15, 11, 0, 0),
        next_audit_date=datetime(2024, 9, 15, 11, 0, 0),
        total_documents=15,
        valid_documents=13,
        expired_documents=0,
        expiring_soon_documents=2,
        missing_required_documents=0,
        compliance_score=88.0,
        notes="Pending review of updated safety training certificates.",
        last_checked_at=datetime(2024, 3, 26, 12, 0, 0)
    ),
    SupplierCompliance(
        supplier_id=5,
        supplier_name="Inactive Supplier Co.",
        compliance_status=ComplianceStatus.SUSPENDED,
        last_audit_date=datetime(2023, 6, 1, 10, 0, 0),
        next_audit_date=None,
        total_documents=5,
        valid_documents=0,
        expired_documents=5,
        expiring_soon_documents=0,
        missing_required_documents=3,
        compliance_score=0.0,
        notes="Supplier suspended due to expired documents and missing required certifications.",
        last_checked_at=datetime(2024, 1, 5, 9, 0, 0)
    )
]


@router.get(
    "/suppliers/{id}",
    response_model=SupplierCompliance,
    summary="Get Supplier Compliance Status",
    description="Retrieve detailed compliance status for a specific supplier by ID."
)
@limiter.limit("100/minute")
async def get_supplier_compliance(
    request: Request,
    id: int = Path(..., ge=1, description="Supplier ID")
):
    """
    Get compliance status for a specific supplier.

    **Path Parameters:**
    - **id**: Supplier ID (must be a positive integer)

    **Returns:**
    - Detailed compliance information including:
        - Compliance status (compliant, non_compliant, pending, suspended)
        - Audit dates (last and next scheduled)
        - Document counts (total, valid, expired, expiring soon, missing required)
        - Compliance score (0-100)
        - Additional notes

    **Example:**
    ```
    GET /api/v1/compliance/suppliers/1
    ```

    **Response:**
    ```json
    {
        "supplier_id": 1,
        "supplier_name": "ABC Construction Supplies Ltd.",
        "compliance_status": "compliant",
        "last_audit_date": "2024-02-15T10:00:00Z",
        "next_audit_date": "2024-08-15T10:00:00Z",
        "total_documents": 12,
        "valid_documents": 11,
        "expired_documents": 0,
        "expiring_soon_documents": 1,
        "missing_required_documents": 0,
        "compliance_score": 95.5,
        "notes": "Annual audit completed. One document expiring in 30 days.",
        "last_checked_at": "2024-03-20T14:45:00Z"
    }
    ```

    **Error Responses:**
    - **404 Not Found**: Supplier ID not found
    - **429 Too Many Requests**: Rate limit exceeded
    """
    # Find compliance data for the supplier
    compliance = next(
        (c for c in MOCK_COMPLIANCE_DATA if c.supplier_id == id),
        None
    )

    if compliance is None:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance data not found for supplier ID: {id}"
        )

    return compliance
