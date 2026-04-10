"""
ExpiryAlert Pydantic model

Defines data model for document expiry alerts and notifications.
Used by API endpoints to alert about documents expiring soon.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    """
    Alert severity level enumeration.

    - CRITICAL: Document expired or expiring within 7 days
    - WARNING: Document expiring within 30 days
    - INFO: Document expiring within 90 days
    """
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ExpiryAlert(BaseModel):
    """
    Expiry alert model representing a document expiry notification.

    Contains information about a document that is expired or expiring soon,
    including supplier details, document information, and severity level.
    Used by expiry alert endpoints to warn about upcoming document expirations.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "document_id": 123,
                "document_name": "General Liability Insurance Certificate",
                "document_type": "insurance",
                "supplier_id": 1,
                "supplier_name": "ABC Construction Supplies Ltd.",
                "expiry_date": "2024-04-20T00:00:00Z",
                "days_until_expiry": 10,
                "severity": "warning",
                "is_required": True,
                "alert_sent": True,
                "alert_sent_at": "2024-04-01T09:00:00Z",
                "created_at": "2024-04-01T09:00:00Z",
                "updated_at": "2024-04-01T09:00:00Z"
            }
        }
    )

    id: int = Field(..., description="Unique alert identifier", gt=0)
    document_id: int = Field(..., description="Associated document ID", gt=0)
    document_name: str = Field(..., description="Document name for reference", min_length=1, max_length=255)
    document_type: str = Field(..., description="Type of document", max_length=50)
    supplier_id: int = Field(..., description="Associated supplier ID", gt=0)
    supplier_name: str = Field(..., description="Supplier name for reference", min_length=1, max_length=255)
    expiry_date: datetime = Field(..., description="Date when the document expires")
    days_until_expiry: int = Field(..., description="Number of days until expiry (negative if expired)")
    severity: AlertSeverity = Field(..., description="Alert severity level based on time until expiry")
    is_required: bool = Field(False, description="Whether the document is required for compliance")
    alert_sent: bool = Field(False, description="Whether an alert notification has been sent")
    alert_sent_at: Optional[datetime] = Field(None, description="Timestamp when alert notification was sent")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ExpiryAlertSummary(BaseModel):
    """
    Expiry alert summary model.

    Contains aggregated statistics about expiry alerts in the system,
    grouped by severity and document type. Used by alert summary
    endpoints to provide quick overview of pending alerts.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_alerts": 25,
                "critical_alerts": 5,
                "warning_alerts": 12,
                "info_alerts": 8,
                "alerts_by_type": {
                    "insurance": 8,
                    "tax": 6,
                    "license": 5,
                    "registration": 3,
                    "quality": 2,
                    "safety": 1
                },
                "unsent_alerts": 3,
                "suppliers_affected": 18,
                "required_documents_expiring": 15,
                "last_checked_at": "2024-04-10T14:30:00Z"
            }
        }
    )

    total_alerts: int = Field(0, description="Total number of active alerts", ge=0)
    critical_alerts: int = Field(0, description="Number of critical alerts (expired or <7 days)", ge=0)
    warning_alerts: int = Field(0, description="Number of warning alerts (<30 days)", ge=0)
    info_alerts: int = Field(0, description="Number of info alerts (<90 days)", ge=0)
    alerts_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Alert counts grouped by document type"
    )
    unsent_alerts: int = Field(0, description="Number of alerts that haven't been sent yet", ge=0)
    suppliers_affected: int = Field(0, description="Number of unique suppliers with expiring documents", ge=0)
    required_documents_expiring: int = Field(0, description="Number of required documents expiring", ge=0)
    last_checked_at: datetime = Field(..., description="Timestamp when alerts were last calculated")
