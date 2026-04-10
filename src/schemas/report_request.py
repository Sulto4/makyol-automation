"""Pydantic schemas for report requests."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date


class ReportRequest(BaseModel):
    """Schema for report generation request."""

    report_type: Literal[
        "supplier_summary",
        "document_inventory",
        "expiring_certificates",
        "missing_documents",
        "full_audit"
    ] = Field(
        ...,
        description="Type of report to generate"
    )

    format: Literal["pdf", "excel"] = Field(
        ...,
        description="Report format (PDF or Excel)"
    )

    preparer: str = Field(
        ...,
        description="Name of the person generating the report",
        min_length=1
    )

    # Optional filters
    supplier_id: Optional[int] = Field(
        None,
        description="Filter by specific supplier ID"
    )

    date_from: Optional[date] = Field(
        None,
        description="Filter documents from this date"
    )

    date_to: Optional[date] = Field(
        None,
        description="Filter documents up to this date"
    )

    status: Optional[Literal["valid", "expired", "missing", "pending"]] = Field(
        None,
        description="Filter by document status"
    )

    days_threshold: Optional[int] = Field(
        30,
        description="Days threshold for expiring certificates report",
        ge=1,
        le=365
    )

    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "supplier_summary",
                "format": "pdf",
                "preparer": "John Doe",
                "supplier_id": None,
                "date_from": None,
                "date_to": None,
                "status": None,
                "days_threshold": 30
            }
        }
