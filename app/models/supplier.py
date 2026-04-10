"""
Supplier and SupplierCompliance Pydantic models

Defines data models for supplier information and compliance status.
Used by API endpoints to validate requests and format responses.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ComplianceStatus(str, Enum):
    """
    Supplier compliance status enumeration.

    - COMPLIANT: All documents are valid and up to date
    - NON_COMPLIANT: One or more required documents are missing or expired
    - PENDING: Compliance review is in progress
    - SUSPENDED: Supplier is temporarily suspended due to compliance issues
    """
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    SUSPENDED = "suspended"


class SupplierCategory(str, Enum):
    """
    Supplier category classification.

    - CONSTRUCTION: Construction materials and services
    - EQUIPMENT: Equipment suppliers and rental
    - CONSULTING: Consulting and professional services
    - LABOR: Labor contractors
    - OTHER: Other supplier types
    """
    CONSTRUCTION = "construction"
    EQUIPMENT = "equipment"
    CONSULTING = "consulting"
    LABOR = "labor"
    OTHER = "other"


class Supplier(BaseModel):
    """
    Supplier model representing a company or individual providing goods/services.

    Contains basic supplier information, contact details, and registration data.
    Used for supplier listing and detail endpoints.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "ABC Construction Supplies Ltd.",
                "registration_number": "CR-2023-45678",
                "tax_id": "TR-987654321",
                "category": "construction",
                "email": "contact@abcconstruction.com",
                "phone": "+40-21-555-0123",
                "address": "123 Industrial Park, Bucharest, Romania",
                "contact_person": "John Popescu",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-03-20T14:45:00Z"
            }
        }
    )

    id: int = Field(..., description="Unique supplier identifier", gt=0)
    name: str = Field(..., description="Supplier company name", min_length=1, max_length=255)
    registration_number: Optional[str] = Field(None, description="Company registration number", max_length=100)
    tax_id: Optional[str] = Field(None, description="Tax identification number", max_length=100)
    category: SupplierCategory = Field(..., description="Supplier category/type")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone number", max_length=50)
    address: Optional[str] = Field(None, description="Registered business address", max_length=500)
    contact_person: Optional[str] = Field(None, description="Primary contact person name", max_length=255)
    is_active: bool = Field(True, description="Whether supplier is currently active")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SupplierCompliance(BaseModel):
    """
    Supplier compliance status model.

    Contains detailed compliance information including document counts,
    audit dates, and overall compliance status. Used by compliance
    status endpoints to provide comprehensive compliance overview.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    supplier_id: int = Field(..., description="Supplier identifier", gt=0)
    supplier_name: str = Field(..., description="Supplier name for reference", min_length=1, max_length=255)
    compliance_status: ComplianceStatus = Field(..., description="Current compliance status")
    last_audit_date: Optional[datetime] = Field(None, description="Date of last compliance audit")
    next_audit_date: Optional[datetime] = Field(None, description="Date of next scheduled audit")
    total_documents: int = Field(0, description="Total number of documents on file", ge=0)
    valid_documents: int = Field(0, description="Number of valid, non-expired documents", ge=0)
    expired_documents: int = Field(0, description="Number of expired documents", ge=0)
    expiring_soon_documents: int = Field(0, description="Number of documents expiring within 30 days", ge=0)
    missing_required_documents: int = Field(0, description="Number of required documents not on file", ge=0)
    compliance_score: Optional[float] = Field(
        None,
        description="Compliance score (0-100) based on document validity",
        ge=0.0,
        le=100.0
    )
    notes: Optional[str] = Field(None, description="Additional compliance notes or comments", max_length=1000)
    last_checked_at: datetime = Field(..., description="Timestamp when compliance status was last calculated")


class SupplierCreate(BaseModel):
    """
    Supplier creation model (for future POST endpoint).

    Contains required fields for creating a new supplier.
    Excludes auto-generated fields like id, created_at, updated_at.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "XYZ Equipment Rental",
                "registration_number": "CR-2024-12345",
                "tax_id": "TR-123456789",
                "category": "equipment",
                "email": "info@xyzrental.com",
                "phone": "+40-21-555-9876",
                "address": "456 Business District, Cluj-Napoca, Romania",
                "contact_person": "Maria Ionescu",
                "is_active": True
            }
        }
    )

    name: str = Field(..., description="Supplier company name", min_length=1, max_length=255)
    registration_number: Optional[str] = Field(None, description="Company registration number", max_length=100)
    tax_id: Optional[str] = Field(None, description="Tax identification number", max_length=100)
    category: SupplierCategory = Field(..., description="Supplier category/type")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone number", max_length=50)
    address: Optional[str] = Field(None, description="Registered business address", max_length=500)
    contact_person: Optional[str] = Field(None, description="Primary contact person name", max_length=255)
    is_active: bool = Field(True, description="Whether supplier is currently active")


class SupplierUpdate(BaseModel):
    """
    Supplier update model (for future PATCH/PUT endpoint).

    Contains optional fields for updating an existing supplier.
    All fields are optional to support partial updates.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newemail@supplier.com",
                "phone": "+40-21-555-1111",
                "is_active": False
            }
        }
    )

    name: Optional[str] = Field(None, description="Supplier company name", min_length=1, max_length=255)
    registration_number: Optional[str] = Field(None, description="Company registration number", max_length=100)
    tax_id: Optional[str] = Field(None, description="Tax identification number", max_length=100)
    category: Optional[SupplierCategory] = Field(None, description="Supplier category/type")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone number", max_length=50)
    address: Optional[str] = Field(None, description="Registered business address", max_length=500)
    contact_person: Optional[str] = Field(None, description="Primary contact person name", max_length=255)
    is_active: Optional[bool] = Field(None, description="Whether supplier is currently active")
