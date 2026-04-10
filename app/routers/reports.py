"""
Reports Router

Provides endpoints for generating compliance reports:
- GET /api/v1/reports/compliance - Generate compliance report with statistics and insights

Supports multiple output formats (JSON, PDF, CSV, Excel) and customizable reporting periods.
"""

from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from app.middleware.rate_limit import limiter
from app.models.report import ComplianceReport, ReportFormat, ReportPeriod, SupplierComplianceSummary

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"]
)


# Mock data for compliance report (to be replaced with database queries)
MOCK_COMPLIANCE_REPORT = ComplianceReport(
    id=1,
    report_name="Current Compliance Status Report",
    report_period=ReportPeriod.CURRENT,
    period_start=datetime(2024, 1, 1, 0, 0, 0),
    period_end=datetime(2024, 4, 10, 23, 59, 59),
    generated_at=datetime.now(),
    generated_by="system@makyol.com",

    # Supplier statistics
    total_suppliers=5,
    compliant_suppliers=3,
    non_compliant_suppliers=1,
    pending_suppliers=0,
    suspended_suppliers=1,

    # Document statistics
    total_documents=125,
    valid_documents=98,
    expired_documents=12,
    expiring_soon_documents=8,
    pending_review_documents=7,

    # Compliance metrics
    overall_compliance_rate=78.4,
    compliance_trend=2.5,
    critical_issues=3,
    warnings=15,

    # Detailed breakdowns
    top_non_compliant_suppliers=[
        SupplierComplianceSummary(
            supplier_id=5,
            supplier_name="Inactive Supplier Co.",
            compliance_status="suspended",
            compliance_score=0.0,
            total_documents=8,
            expired_documents=8,
            expiring_soon_documents=0
        )
    ],
    documents_by_type={
        "insurance": 25,
        "tax": 20,
        "license": 18,
        "safety": 15,
        "environmental": 12,
        "quality": 10,
        "other": 25
    },

    # Forecasting
    expiry_forecast_30_days=8,
    expiry_forecast_60_days=12,
    expiry_forecast_90_days=18,

    # Recommendations
    recommendations=[
        "Review 1 non-compliant supplier urgently",
        "Renew 8 documents expiring in 30 days",
        "Follow up on 7 documents pending review",
        "Address 3 critical compliance issues immediately"
    ],
    notes="Overall compliance rate is healthy at 78.4%, showing improvement of 2.5 percentage points compared to previous period."
)


@router.get(
    "/compliance",
    response_model=ComplianceReport,
    summary="Generate Compliance Report",
    description="Generate a comprehensive compliance report with statistics, trends, and recommendations."
)
@limiter.limit("100/minute")
async def get_compliance_report(
    request: Request,
    format: ReportFormat = Query(
        ReportFormat.JSON,
        description="Report output format (json, pdf, csv, excel)"
    ),
    period: Optional[ReportPeriod] = Query(
        None,
        description="Report period (current, weekly, monthly, quarterly, yearly, custom)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Custom period start date (ISO 8601 format, required if period=custom)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Custom period end date (ISO 8601 format, required if period=custom)"
    )
):
    """
    Generate a comprehensive compliance report.

    **Query Parameters:**
    - **format**: Output format (json, pdf, csv, excel) - default: json
    - **period**: Report period (current, weekly, monthly, quarterly, yearly, custom) - default: current
    - **start_date**: Custom period start date (required if period=custom)
    - **end_date**: Custom period end date (required if period=custom)

    **Returns:**
    - Comprehensive compliance report with:
      - Supplier compliance statistics and trends
      - Document inventory and expiry forecasts
      - Compliance metrics and scores
      - Critical issues and warnings
      - Automated recommendations

    **Notes:**
    - For format=json, returns the report as JSON (current implementation)
    - Other formats (pdf, csv, excel) will be supported in future versions
    - Custom date ranges require both start_date and end_date parameters

    **Example:**
    ```
    GET /api/v1/reports/compliance?format=json&period=current
    GET /api/v1/reports/compliance?format=pdf&period=quarterly
    GET /api/v1/reports/compliance?format=json&period=custom&start_date=2024-01-01T00:00:00Z&end_date=2024-03-31T23:59:59Z
    ```
    """
    # Validate custom period parameters
    if period == ReportPeriod.CUSTOM:
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="Both start_date and end_date are required when period=custom"
            )
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )

    # For non-JSON formats, return a note that they're not yet implemented
    if format != ReportFormat.JSON:
        raise HTTPException(
            status_code=501,
            detail=f"Format '{format}' is not yet implemented. Currently only 'json' format is supported."
        )

    # Clone the mock report and update timestamps
    report = MOCK_COMPLIANCE_REPORT.model_copy(deep=True)
    report.generated_at = datetime.now()

    # Update report period if specified
    if period:
        report.report_period = period

        # Adjust period dates based on period type
        if period == ReportPeriod.CURRENT:
            report.period_start = datetime(2024, 1, 1, 0, 0, 0)
            report.period_end = datetime.now()
            report.report_name = "Current Compliance Status Report"
        elif period == ReportPeriod.WEEKLY:
            report.period_end = datetime.now()
            report.period_start = report.period_end - timedelta(days=7)
            report.report_name = "Weekly Compliance Report"
        elif period == ReportPeriod.MONTHLY:
            report.period_end = datetime.now()
            report.period_start = report.period_end - timedelta(days=30)
            report.report_name = "Monthly Compliance Report"
        elif period == ReportPeriod.QUARTERLY:
            report.period_end = datetime.now()
            report.period_start = report.period_end - timedelta(days=90)
            report.report_name = "Quarterly Compliance Report"
        elif period == ReportPeriod.YEARLY:
            report.period_end = datetime.now()
            report.period_start = report.period_end - timedelta(days=365)
            report.report_name = "Yearly Compliance Report"
        elif period == ReportPeriod.CUSTOM:
            report.period_start = start_date
            report.period_end = end_date
            report.report_name = f"Custom Compliance Report ({start_date.date()} to {end_date.date()})"

    return report
