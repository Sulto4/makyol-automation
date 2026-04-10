"""
Compliance API Endpoint Tests

Tests for compliance endpoints including:
- Get supplier compliance status by ID
- Compliance status values and scoring
- Document statistics
- Audit date handling
- Error handling and validation
"""

import pytest
from fastapi import status


class TestGetSupplierCompliance:
    """Test GET /api/v1/compliance/suppliers/{id} endpoint."""

    def test_get_compliance_success(self, client, auth_headers):
        """Should return compliance status for valid supplier ID."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "supplier_id" in data
        assert "supplier_name" in data
        assert "compliance_status" in data
        assert "compliance_score" in data
        assert data["supplier_id"] == 1

    def test_get_compliance_response_structure(self, client, auth_headers):
        """Should return complete compliance information."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Basic fields
        assert "supplier_id" in data
        assert "supplier_name" in data
        assert "compliance_status" in data

        # Audit dates
        assert "last_audit_date" in data
        assert "next_audit_date" in data

        # Document counts
        assert "total_documents" in data
        assert "valid_documents" in data
        assert "expired_documents" in data
        assert "expiring_soon_documents" in data
        assert "missing_required_documents" in data

        # Compliance metrics
        assert "compliance_score" in data

        # Metadata
        assert "last_checked_at" in data

    def test_get_compliance_not_found(self, client, auth_headers):
        """Should return 404 for non-existent supplier."""
        response = client.get(
            "/api/v1/compliance/suppliers/999999",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = data.get("error") or data.get("message")
        assert "999999" in error_msg

    def test_get_compliance_data_types(self, client, auth_headers):
        """Should return correct data types."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data["supplier_id"], int)
        assert isinstance(data["supplier_name"], str)
        assert isinstance(data["compliance_status"], str)
        assert isinstance(data["total_documents"], int)
        assert isinstance(data["valid_documents"], int)
        assert isinstance(data["expired_documents"], int)
        assert isinstance(data["compliance_score"], (int, float))


class TestComplianceStatuses:
    """Test different compliance status values."""

    def test_compliant_supplier(self, client, auth_headers):
        """Should return compliant status for supplier 1."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "compliant"
        assert data["compliance_score"] > 0

    def test_non_compliant_supplier(self, client, auth_headers):
        """Should return non-compliant status for supplier 3."""
        response = client.get(
            "/api/v1/compliance/suppliers/3",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "non_compliant"
        assert data["expired_documents"] > 0 or data["missing_required_documents"] > 0

    def test_pending_supplier(self, client, auth_headers):
        """Should return pending status for supplier 4."""
        response = client.get(
            "/api/v1/compliance/suppliers/4",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "pending"

    def test_suspended_supplier(self, client, auth_headers):
        """Should return suspended status for supplier 5."""
        response = client.get(
            "/api/v1/compliance/suppliers/5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "suspended"
        assert data["compliance_score"] == 0.0


class TestComplianceDocumentCounts:
    """Test document count statistics."""

    def test_document_counts_sum(self, client, auth_headers):
        """Document counts should be logical."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total_documents"] >= 0
        assert data["valid_documents"] >= 0
        assert data["expired_documents"] >= 0
        assert data["expiring_soon_documents"] >= 0
        assert data["missing_required_documents"] >= 0

        # Valid + Expired + Expiring Soon should be <= Total
        # (some documents may be in other states like pending_review)
        counted = (
            data["valid_documents"] +
            data["expired_documents"] +
            data["expiring_soon_documents"]
        )
        assert counted <= data["total_documents"]

    def test_fully_compliant_has_no_issues(self, client, auth_headers):
        """Compliant supplier 2 should have no expired or missing documents."""
        response = client.get(
            "/api/v1/compliance/suppliers/2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "compliant"
        assert data["expired_documents"] == 0
        assert data["missing_required_documents"] == 0

    def test_non_compliant_has_issues(self, client, auth_headers):
        """Non-compliant supplier should have issues."""
        response = client.get(
            "/api/v1/compliance/suppliers/3",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_status"] == "non_compliant"
        # Should have at least one issue
        assert (
            data["expired_documents"] > 0 or
            data["missing_required_documents"] > 0
        )


class TestComplianceScoring:
    """Test compliance score calculations."""

    def test_compliance_score_range(self, client, auth_headers):
        """Compliance score should be between 0 and 100."""
        for supplier_id in [1, 2, 3, 4, 5]:
            response = client.get(
                f"/api/v1/compliance/suppliers/{supplier_id}",
                headers=auth_headers
            )
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert 0.0 <= data["compliance_score"] <= 100.0

    def test_perfect_score(self, client, auth_headers):
        """Fully compliant supplier should have high score."""
        response = client.get(
            "/api/v1/compliance/suppliers/2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_score"] == 100.0

    def test_suspended_has_zero_score(self, client, auth_headers):
        """Suspended supplier should have zero score."""
        response = client.get(
            "/api/v1/compliance/suppliers/5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["compliance_score"] == 0.0


class TestComplianceAuditDates:
    """Test audit date handling."""

    def test_audit_dates_present(self, client, auth_headers):
        """Should include audit dates in response."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "last_audit_date" in data
        assert "next_audit_date" in data

    def test_suspended_supplier_no_next_audit(self, client, auth_headers):
        """Suspended supplier may not have next audit date."""
        response = client.get(
            "/api/v1/compliance/suppliers/5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["next_audit_date"] is None


class TestComplianceAuthentication:
    """Test authentication requirements."""

    def test_compliance_requires_auth(self, client):
        """Compliance endpoint should require authentication."""
        response = client.get("/api/v1/compliance/suppliers/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_compliance_with_invalid_api_key(self, client, invalid_auth_headers):
        """Should reject invalid API key."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=invalid_auth_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestComplianceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_invalid_supplier_id(self, client, auth_headers):
        """Should reject invalid supplier ID."""
        response = client.get(
            "/api/v1/compliance/suppliers/0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_negative_supplier_id(self, client, auth_headers):
        """Should reject negative supplier ID."""
        response = client.get(
            "/api/v1/compliance/suppliers/-1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_compliance_notes_field(self, client, auth_headers):
        """Should include notes field with compliance details."""
        response = client.get(
            "/api/v1/compliance/suppliers/1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "notes" in data
        if data["notes"]:
            assert isinstance(data["notes"], str)
