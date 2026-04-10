"""
Reports API Endpoint Tests

Tests for reports endpoints including:
- Generate compliance report
- Report periods (current, weekly, monthly, quarterly, yearly, custom)
- Report formats (JSON, PDF, CSV, Excel)
- Report statistics and metrics
- Custom date ranges
- Error handling and validation
"""

import pytest
from fastapi import status
from datetime import datetime


class TestComplianceReport:
    """Test GET /api/v1/reports/compliance endpoint."""

    def test_compliance_report_basic(self, client, auth_headers):
        """Should generate basic compliance report."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "id" in data
        assert "report_name" in data
        assert "generated_at" in data

    def test_compliance_report_structure(self, client, auth_headers):
        """Should return complete report structure."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Basic info
        assert "id" in data
        assert "report_name" in data
        assert "report_period" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "generated_at" in data
        assert "generated_by" in data

        # Supplier statistics
        assert "total_suppliers" in data
        assert "compliant_suppliers" in data
        assert "non_compliant_suppliers" in data
        assert "pending_suppliers" in data
        assert "suspended_suppliers" in data

        # Document statistics
        assert "total_documents" in data
        assert "valid_documents" in data
        assert "expired_documents" in data
        assert "expiring_soon_documents" in data
        assert "pending_review_documents" in data

        # Compliance metrics
        assert "overall_compliance_rate" in data
        assert "compliance_trend" in data
        assert "critical_issues" in data
        assert "warnings" in data

    def test_compliance_report_statistics(self, client, auth_headers):
        """Should include compliance statistics."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Check data types
        assert isinstance(data["total_suppliers"], int)
        assert isinstance(data["compliant_suppliers"], int)
        assert isinstance(data["total_documents"], int)
        assert isinstance(data["overall_compliance_rate"], (int, float))

        # Check logical constraints
        assert data["total_suppliers"] >= 0
        assert data["compliant_suppliers"] <= data["total_suppliers"]
        assert 0 <= data["overall_compliance_rate"] <= 100


class TestReportPeriods:
    """Test different report periods."""

    def test_current_period(self, client, auth_headers):
        """Should generate report for current period."""
        response = client.get(
            "/api/v1/reports/compliance?period=current",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "current"

    def test_weekly_period(self, client, auth_headers):
        """Should generate weekly report."""
        response = client.get(
            "/api/v1/reports/compliance?period=weekly",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "weekly"

    def test_monthly_period(self, client, auth_headers):
        """Should generate monthly report."""
        response = client.get(
            "/api/v1/reports/compliance?period=monthly",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "monthly"

    def test_quarterly_period(self, client, auth_headers):
        """Should generate quarterly report."""
        response = client.get(
            "/api/v1/reports/compliance?period=quarterly",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "quarterly"

    def test_yearly_period(self, client, auth_headers):
        """Should generate yearly report."""
        response = client.get(
            "/api/v1/reports/compliance?period=yearly",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "yearly"


class TestCustomPeriod:
    """Test custom date range reporting."""

    def test_custom_period_valid(self, client, auth_headers):
        """Should generate report for custom date range."""
        response = client.get(
            "/api/v1/reports/compliance?period=custom&start_date=2024-01-01T00:00:00Z&end_date=2024-03-31T23:59:59Z",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["report_period"] == "custom"

    def test_custom_period_missing_start_date(self, client, auth_headers):
        """Should reject custom period without start_date."""
        response = client.get(
            "/api/v1/reports/compliance?period=custom&end_date=2024-03-31T23:59:59Z",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = (data.get("error") or data.get("message")).lower()
        assert "start_date" in error_msg

    def test_custom_period_missing_end_date(self, client, auth_headers):
        """Should reject custom period without end_date."""
        response = client.get(
            "/api/v1/reports/compliance?period=custom&start_date=2024-01-01T00:00:00Z",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = (data.get("error") or data.get("message")).lower()
        assert "end_date" in error_msg

    def test_custom_period_invalid_range(self, client, auth_headers):
        """Should reject custom period where start_date >= end_date."""
        response = client.get(
            "/api/v1/reports/compliance?period=custom&start_date=2024-03-31T00:00:00Z&end_date=2024-01-01T00:00:00Z",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "error" in data or "message" in data


class TestReportFormats:
    """Test different report output formats."""

    def test_json_format(self, client, auth_headers):
        """Should generate report in JSON format."""
        response = client.get(
            "/api/v1/reports/compliance?format=json",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), dict)

    def test_pdf_format_not_implemented(self, client, auth_headers):
        """PDF format should return not implemented."""
        response = client.get(
            "/api/v1/reports/compliance?format=pdf",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = (data.get("error") or data.get("message")).lower()
        assert "pdf" in error_msg

    def test_csv_format_not_implemented(self, client, auth_headers):
        """CSV format should return not implemented."""
        response = client.get(
            "/api/v1/reports/compliance?format=csv",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_excel_format_not_implemented(self, client, auth_headers):
        """Excel format should return not implemented."""
        response = client.get(
            "/api/v1/reports/compliance?format=excel",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestReportMetrics:
    """Test report metrics and calculations."""

    def test_supplier_count_sum(self, client, auth_headers):
        """Supplier category counts should sum to total."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        total = data["total_suppliers"]
        sum_categories = (
            data["compliant_suppliers"] +
            data["non_compliant_suppliers"] +
            data["pending_suppliers"] +
            data["suspended_suppliers"]
        )
        assert sum_categories == total

    def test_document_statistics(self, client, auth_headers):
        """Document statistics should be logical."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total_documents"] >= 0
        assert data["valid_documents"] >= 0
        assert data["expired_documents"] >= 0
        assert data["expiring_soon_documents"] >= 0

        # Valid + Expired + Expiring Soon + Pending Review should be <= Total
        counted = (
            data["valid_documents"] +
            data["expired_documents"] +
            data["expiring_soon_documents"] +
            data["pending_review_documents"]
        )
        assert counted <= data["total_documents"]

    def test_compliance_rate_range(self, client, auth_headers):
        """Compliance rate should be between 0 and 100."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert 0 <= data["overall_compliance_rate"] <= 100

    def test_critical_issues_count(self, client, auth_headers):
        """Critical issues count should be non-negative."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["critical_issues"] >= 0
        assert data["warnings"] >= 0


class TestReportDetails:
    """Test detailed report sections."""

    def test_top_non_compliant_suppliers(self, client, auth_headers):
        """Should include top non-compliant suppliers."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "top_non_compliant_suppliers" in data
        assert isinstance(data["top_non_compliant_suppliers"], list)

        if len(data["top_non_compliant_suppliers"]) > 0:
            supplier = data["top_non_compliant_suppliers"][0]
            assert "supplier_id" in supplier
            assert "supplier_name" in supplier
            assert "compliance_status" in supplier
            assert "compliance_score" in supplier

    def test_documents_by_type(self, client, auth_headers):
        """Should include document breakdown by type."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "documents_by_type" in data
        assert isinstance(data["documents_by_type"], dict)

    def test_expiry_forecast(self, client, auth_headers):
        """Should include expiry forecasts."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "expiry_forecast_30_days" in data
        assert "expiry_forecast_60_days" in data
        assert "expiry_forecast_90_days" in data

        # Forecasts should be cumulative
        assert data["expiry_forecast_30_days"] >= 0
        assert data["expiry_forecast_60_days"] >= data["expiry_forecast_30_days"]
        assert data["expiry_forecast_90_days"] >= data["expiry_forecast_60_days"]

    def test_recommendations(self, client, auth_headers):
        """Should include actionable recommendations."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestReportsAuthentication:
    """Test authentication requirements."""

    def test_reports_requires_auth(self, client):
        """Reports endpoint should require authentication."""
        response = client.get("/api/v1/reports/compliance")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reports_with_invalid_api_key(self, client, invalid_auth_headers):
        """Should reject invalid API key."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=invalid_auth_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReportsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generated_at_timestamp(self, client, auth_headers):
        """Generated_at should be recent timestamp."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Should have a timestamp
        assert data["generated_at"] is not None

    def test_notes_field(self, client, auth_headers):
        """Should include notes field."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "notes" in data
        if data["notes"]:
            assert isinstance(data["notes"], str)

    def test_compliance_trend(self, client, auth_headers):
        """Should include compliance trend."""
        response = client.get(
            "/api/v1/reports/compliance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "compliance_trend" in data
        assert isinstance(data["compliance_trend"], (int, float))
