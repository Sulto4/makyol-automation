"""
ComplianceReport Pydantic model

Defines data model for compliance reports and analytics.
Used by API endpoints to generate comprehensive compliance reports.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    """
    Report format enumeration.

    - JSON: JSON format for API consumption
    - PDF: PDF format for printing and archival
    - CSV: CSV format for data analysis and Excel import
    - EXCEL: Excel format with multiple sheets and formatting
    """
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class ReportPeriod(str, Enum):
    """
    Report period enumeration.

    - CURRENT: Current compliance status snapshot
    - WEEKLY: Last 7 days
    - MONTHLY: Last 30 days
    - QUARTERLY: Last 90 days
    - YEARLY: Last 365 days
    - CUSTOM: Custom date range
    """
    CURRENT = "current"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class SupplierComplianceSummary(BaseModel):
    """
    Supplier compliance summary for report inclusion.

    Condensed version of supplier compliance information
    for use within compliance reports.
    """
    supplier_id: int = Field(..., description="Supplier identifier", gt=0)
    supplier_name: str = Field(..., description="Supplier name", min_length=1, max_length=255)
    compliance_status: str = Field(..., description="Current compliance status", max_length=50)
    compliance_score: Optional[float] = Field(
        None,
        description="Compliance score (0-100)",
        ge=0.0,
        le=100.0
    )
    total_documents: int = Field(0, description="Total documents on file", ge=0)
    expired_documents: int = Field(0, description="Number of expired documents", ge=0)
    expiring_soon_documents: int = Field(0, description="Number of documents expiring soon", ge=0)


class ComplianceReport(BaseModel):
    """
    Compliance report model representing a comprehensive compliance analysis.

    Contains aggregated compliance data, statistics, and trends across all
    suppliers and documents. Used by compliance report endpoints to provide
    detailed compliance insights for management and auditing.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "report_name": "Q1 2024 Compliance Report",
                "report_period": "quarterly",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-03-31T23:59:59Z",
                "generated_at": "2024-04-01T10:00:00Z",
                "generated_by": "admin@makyol.com",
                "total_suppliers": 45,
                "compliant_suppliers": 38,
                "non_compliant_suppliers": 7,
                "pending_suppliers": 0,
                "suspended_suppliers": 0,
                "total_documents": 125,
                "valid_documents": 98,
                "expired_documents": 12,
                "expiring_soon_documents": 8,
                "pending_review_documents": 5,
                "overall_compliance_rate": 84.4,
                "compliance_trend": 2.5,
                "critical_issues": 3,
                "warnings": 15,
                "top_non_compliant_suppliers": [],
                "documents_by_type": {
                    "insurance": 25,
                    "tax": 20,
                    "license": 18
                },
                "expiry_forecast_30_days": 8,
                "expiry_forecast_60_days": 12,
                "expiry_forecast_90_days": 18,
                "recommendations": [
                    "Review 7 non-compliant suppliers urgently",
                    "Renew 8 documents expiring in 30 days"
                ],
                "notes": "Overall compliance improving compared to previous quarter"
            }
        }
    )

    id: int = Field(..., description="Unique report identifier", gt=0)
    report_name: str = Field(..., description="Report title/name", min_length=1, max_length=255)
    report_period: ReportPeriod = Field(..., description="Report period type")
    period_start: datetime = Field(..., description="Start date of reporting period")
    period_end: datetime = Field(..., description="End date of reporting period")
    generated_at: datetime = Field(..., description="Timestamp when report was generated")
    generated_by: Optional[str] = Field(None, description="User who generated the report", max_length=255)

    # Supplier statistics
    total_suppliers: int = Field(0, description="Total number of suppliers", ge=0)
    compliant_suppliers: int = Field(0, description="Number of compliant suppliers", ge=0)
    non_compliant_suppliers: int = Field(0, description="Number of non-compliant suppliers", ge=0)
    pending_suppliers: int = Field(0, description="Number of suppliers pending review", ge=0)
    suspended_suppliers: int = Field(0, description="Number of suspended suppliers", ge=0)

    # Document statistics
    total_documents: int = Field(0, description="Total number of documents", ge=0)
    valid_documents: int = Field(0, description="Number of valid documents", ge=0)
    expired_documents: int = Field(0, description="Number of expired documents", ge=0)
    expiring_soon_documents: int = Field(0, description="Number of documents expiring within 30 days", ge=0)
    pending_review_documents: int = Field(0, description="Number of documents awaiting review", ge=0)

    # Compliance metrics
    overall_compliance_rate: float = Field(
        0.0,
        description="Overall compliance rate percentage (0-100)",
        ge=0.0,
        le=100.0
    )
    compliance_trend: Optional[float] = Field(
        None,
        description="Compliance rate change vs previous period (percentage points)"
    )
    critical_issues: int = Field(0, description="Number of critical compliance issues", ge=0)
    warnings: int = Field(0, description="Number of compliance warnings", ge=0)

    # Detailed breakdowns
    top_non_compliant_suppliers: List[SupplierComplianceSummary] = Field(
        default_factory=list,
        description="List of suppliers with lowest compliance scores"
    )
    documents_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Document counts grouped by type"
    )

    # Forecasting
    expiry_forecast_30_days: int = Field(0, description="Documents expiring in next 30 days", ge=0)
    expiry_forecast_60_days: int = Field(0, description="Documents expiring in next 60 days", ge=0)
    expiry_forecast_90_days: int = Field(0, description="Documents expiring in next 90 days", ge=0)

    # Additional information
    recommendations: List[str] = Field(
        default_factory=list,
        description="Automated recommendations based on compliance analysis"
    )
    notes: Optional[str] = Field(None, description="Additional report notes or commentary", max_length=2000)


class ComplianceReportCreate(BaseModel):
    """
    Compliance report creation model (for future POST endpoint).

    Contains required fields for generating a new compliance report.
    Excludes auto-generated fields and statistics that will be calculated.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_name": "Q2 2024 Compliance Report",
                "report_period": "quarterly",
                "period_start": "2024-04-01T00:00:00Z",
                "period_end": "2024-06-30T23:59:59Z",
                "generated_by": "admin@makyol.com",
                "notes": "Quarterly compliance analysis for Q2 2024"
            }
        }
    )

    report_name: str = Field(..., description="Report title/name", min_length=1, max_length=255)
    report_period: ReportPeriod = Field(..., description="Report period type")
    period_start: datetime = Field(..., description="Start date of reporting period")
    period_end: datetime = Field(..., description="End date of reporting period")
    generated_by: Optional[str] = Field(None, description="User who generated the report", max_length=255)
    notes: Optional[str] = Field(None, description="Additional report notes or commentary", max_length=2000)
