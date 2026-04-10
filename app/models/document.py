"""
Document and DocumentInventory Pydantic models

Defines data models for compliance document information and inventory status.
Used by API endpoints to validate requests and format responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """
    Document type enumeration.

    - REGISTRATION: Company registration documents
    - TAX: Tax compliance documents (tax certificates, VAT registration)
    - INSURANCE: Insurance certificates and policies
    - LICENSE: Business licenses and permits
    - FINANCIAL: Financial statements and reports
    - QUALITY: Quality certifications (ISO, etc.)
    - SAFETY: Safety certifications and compliance documents
    - CONTRACT: Contracts and agreements
    - OTHER: Other document types
    """
    REGISTRATION = "registration"
    TAX = "tax"
    INSURANCE = "insurance"
    LICENSE = "license"
    FINANCIAL = "financial"
    QUALITY = "quality"
    SAFETY = "safety"
    CONTRACT = "contract"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """
    Document status enumeration.

    - VALID: Document is valid and up to date
    - EXPIRED: Document has passed its expiry date
    - EXPIRING_SOON: Document is valid but expiring within 30 days
    - PENDING_REVIEW: Document uploaded but awaiting validation
    - REJECTED: Document was rejected during validation
    - ARCHIVED: Document is archived (superseded by newer version)
    """
    VALID = "valid"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class Document(BaseModel):
    """
    Document model representing a compliance document for a supplier.

    Contains document metadata, supplier relationship, file information,
    and validity dates. Used for document listing and detail endpoints.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "supplier_id": 1,
                "supplier_name": "ABC Construction Supplies Ltd.",
                "document_type": "insurance",
                "document_name": "General Liability Insurance Certificate",
                "file_path": "/uploads/documents/2024/01/insurance_cert_abc_2024.pdf",
                "file_size": 245678,
                "mime_type": "application/pdf",
                "issue_date": "2024-01-01T00:00:00Z",
                "expiry_date": "2025-01-01T00:00:00Z",
                "status": "valid",
                "is_required": True,
                "validation_notes": "Verified on 2024-01-15",
                "uploaded_by": "admin@makyol.com",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )

    id: int = Field(..., description="Unique document identifier", gt=0)
    supplier_id: int = Field(..., description="Associated supplier ID", gt=0)
    supplier_name: str = Field(..., description="Supplier name for reference", min_length=1, max_length=255)
    document_type: DocumentType = Field(..., description="Type/category of document")
    document_name: str = Field(..., description="Document name/title", min_length=1, max_length=255)
    file_path: str = Field(..., description="File storage path", min_length=1, max_length=500)
    file_size: int = Field(..., description="File size in bytes", ge=0)
    mime_type: str = Field(..., description="MIME type of the file", max_length=100)
    issue_date: Optional[datetime] = Field(None, description="Date the document was issued")
    expiry_date: Optional[datetime] = Field(None, description="Date the document expires")
    status: DocumentStatus = Field(..., description="Current document status")
    is_required: bool = Field(False, description="Whether this document is required for compliance")
    validation_notes: Optional[str] = Field(None, description="Notes from document validation/review", max_length=1000)
    uploaded_by: Optional[str] = Field(None, description="Email/username of person who uploaded", max_length=255)
    uploaded_at: datetime = Field(..., description="Timestamp when document was uploaded")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentInventory(BaseModel):
    """
    Document inventory summary model.

    Contains aggregated statistics about documents in the system,
    grouped by status, type, and expiry. Used by inventory and
    summary endpoints to provide document overview.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_documents": 125,
                "valid_documents": 98,
                "expired_documents": 12,
                "expiring_soon_documents": 8,
                "pending_review_documents": 5,
                "rejected_documents": 2,
                "archived_documents": 0,
                "by_type": {
                    "insurance": 25,
                    "tax": 20,
                    "registration": 15,
                    "license": 18,
                    "quality": 12,
                    "safety": 15,
                    "financial": 10,
                    "contract": 8,
                    "other": 2
                },
                "by_supplier": {
                    "total_suppliers": 45,
                    "suppliers_compliant": 38,
                    "suppliers_non_compliant": 7
                },
                "expiry_timeline": {
                    "expiring_7_days": 2,
                    "expiring_30_days": 8,
                    "expiring_90_days": 15
                },
                "last_updated_at": "2024-03-20T14:45:00Z"
            }
        }
    )

    total_documents: int = Field(0, description="Total number of documents in system", ge=0)
    valid_documents: int = Field(0, description="Number of valid, non-expired documents", ge=0)
    expired_documents: int = Field(0, description="Number of expired documents", ge=0)
    expiring_soon_documents: int = Field(0, description="Number of documents expiring within 30 days", ge=0)
    pending_review_documents: int = Field(0, description="Number of documents awaiting review", ge=0)
    rejected_documents: int = Field(0, description="Number of rejected documents", ge=0)
    archived_documents: int = Field(0, description="Number of archived documents", ge=0)
    by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Document counts grouped by type"
    )
    by_supplier: dict[str, int] = Field(
        default_factory=dict,
        description="Supplier-level statistics (total suppliers, compliant, non-compliant)"
    )
    expiry_timeline: dict[str, int] = Field(
        default_factory=dict,
        description="Document counts by expiry timeline (7 days, 30 days, 90 days)"
    )
    last_updated_at: datetime = Field(..., description="Timestamp when inventory was last calculated")


class DocumentCreate(BaseModel):
    """
    Document creation model (for future POST endpoint).

    Contains required fields for uploading a new document.
    Excludes auto-generated fields like id, created_at, updated_at.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "supplier_id": 1,
                "document_type": "insurance",
                "document_name": "Liability Insurance Certificate 2024",
                "file_path": "/uploads/documents/2024/03/insurance_cert_2024.pdf",
                "file_size": 312456,
                "mime_type": "application/pdf",
                "issue_date": "2024-03-01T00:00:00Z",
                "expiry_date": "2025-03-01T00:00:00Z",
                "is_required": True,
                "validation_notes": "Annual insurance renewal",
                "uploaded_by": "procurement@makyol.com"
            }
        }
    )

    supplier_id: int = Field(..., description="Associated supplier ID", gt=0)
    document_type: DocumentType = Field(..., description="Type/category of document")
    document_name: str = Field(..., description="Document name/title", min_length=1, max_length=255)
    file_path: str = Field(..., description="File storage path", min_length=1, max_length=500)
    file_size: int = Field(..., description="File size in bytes", ge=0)
    mime_type: str = Field(..., description="MIME type of the file", max_length=100)
    issue_date: Optional[datetime] = Field(None, description="Date the document was issued")
    expiry_date: Optional[datetime] = Field(None, description="Date the document expires")
    is_required: bool = Field(False, description="Whether this document is required for compliance")
    validation_notes: Optional[str] = Field(None, description="Notes from document validation/review", max_length=1000)
    uploaded_by: Optional[str] = Field(None, description="Email/username of person who uploaded", max_length=255)


class DocumentUpdate(BaseModel):
    """
    Document update model (for future PATCH/PUT endpoint).

    Contains optional fields for updating an existing document.
    All fields are optional to support partial updates.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_name": "Updated Insurance Certificate",
                "expiry_date": "2025-06-01T00:00:00Z",
                "status": "valid",
                "validation_notes": "Extended coverage period"
            }
        }
    )

    document_type: Optional[DocumentType] = Field(None, description="Type/category of document")
    document_name: Optional[str] = Field(None, description="Document name/title", min_length=1, max_length=255)
    file_path: Optional[str] = Field(None, description="File storage path", min_length=1, max_length=500)
    file_size: Optional[int] = Field(None, description="File size in bytes", ge=0)
    mime_type: Optional[str] = Field(None, description="MIME type of the file", max_length=100)
    issue_date: Optional[datetime] = Field(None, description="Date the document was issued")
    expiry_date: Optional[datetime] = Field(None, description="Date the document expires")
    status: Optional[DocumentStatus] = Field(None, description="Current document status")
    is_required: Optional[bool] = Field(None, description="Whether this document is required for compliance")
    validation_notes: Optional[str] = Field(None, description="Notes from document validation/review", max_length=1000)
