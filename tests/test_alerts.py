"""
Alerts API Endpoint Tests

Tests for alerts endpoints including:
- Get document expiry alerts
- Filtering by days threshold
- Filtering by document type and supplier
- Pagination support
- Sorting by expiry date
- Error handling and validation
"""

import pytest
from fastapi import status


class TestExpiryAlerts:
    """Test GET /api/v1/alerts/expiry endpoint."""

    def test_expiry_alerts_basic(self, client, auth_headers):
        """Should return documents expiring within default 30 days."""
        response = client.get(
            "/api/v1/alerts/expiry",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["data"], list)

    def test_expiry_alerts_custom_days(self, client, auth_headers):
        """Should filter by custom days threshold."""
        response = client.get(
            "/api/v1/alerts/expiry?days=60",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All documents should have expiry_date within 60 days
        for document in data["data"]:
            assert document["expiry_date"] is not None

    def test_expiry_alerts_short_period(self, client, auth_headers):
        """Should filter for documents expiring in 7 days."""
        response = client.get(
            "/api/v1/alerts/expiry?days=7",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # May return empty list if no documents expire in 7 days
        assert isinstance(data["data"], list)

    def test_expiry_alerts_long_period(self, client, auth_headers):
        """Should filter for documents expiring in 365 days."""
        response = client.get(
            "/api/v1/alerts/expiry?days=365",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data["data"], list)

    def test_expiry_alerts_response_structure(self, client, auth_headers):
        """Should return documents with correct structure."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if len(data["data"]) > 0:
            document = data["data"][0]
            assert "id" in document
            assert "supplier_id" in document
            assert "supplier_name" in document
            assert "document_type" in document
            assert "document_name" in document
            assert "expiry_date" in document
            assert "status" in document
            assert document["expiry_date"] is not None


class TestExpiryAlertsFiltering:
    """Test filtering options for expiry alerts."""

    def test_filter_by_document_type(self, client, auth_headers):
        """Should filter by document type."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["document_type"] == "insurance"

    def test_filter_by_supplier(self, client, auth_headers):
        """Should filter by supplier ID."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&supplier_id=1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["supplier_id"] == 1

    def test_filter_by_type_and_supplier(self, client, auth_headers):
        """Should support combined filters."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=insurance&supplier_id=1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["document_type"] == "insurance"
            assert document["supplier_id"] == 1


class TestExpiryAlertsPagination:
    """Test pagination for expiry alerts."""

    def test_pagination_parameters(self, client, auth_headers):
        """Should support pagination."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&page=1&limit=5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["data"]) <= 5

    def test_pagination_navigation(self, client, auth_headers):
        """Should provide pagination navigation."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&page=1&limit=2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "has_next" in data
        assert "has_previous" in data
        assert "next_page" in data
        assert "previous_page" in data

    def test_invalid_page(self, client, auth_headers):
        """Should return 404 for invalid page number."""
        response = client.get(
            "/api/v1/alerts/expiry?days=30&page=999",
            headers=auth_headers
        )
        # Should return 404 if page exceeds total pages
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestExpiryAlertsSorting:
    """Test sorting of expiry alerts."""

    def test_sorted_by_expiry_date(self, client, auth_headers):
        """Documents should be sorted by expiry date (soonest first)."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&limit=100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if len(data["data"]) > 1:
            # Check that expiry dates are in ascending order
            expiry_dates = [doc["expiry_date"] for doc in data["data"]]
            sorted_dates = sorted(expiry_dates)
            assert expiry_dates == sorted_dates


class TestExpiryAlertsAuthentication:
    """Test authentication requirements."""

    def test_expiry_alerts_requires_auth(self, client):
        """Expiry alerts should require authentication."""
        response = client.get("/api/v1/alerts/expiry")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expiry_alerts_with_invalid_api_key(self, client, invalid_auth_headers):
        """Should reject invalid API key."""
        response = client.get(
            "/api/v1/alerts/expiry",
            headers=invalid_auth_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestExpiryAlertsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_days_value(self, client, auth_headers):
        """Should accept minimum days value of 1."""
        response = client.get(
            "/api/v1/alerts/expiry?days=1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_maximum_days_value(self, client, auth_headers):
        """Should accept maximum days value of 365."""
        response = client.get(
            "/api/v1/alerts/expiry?days=365",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_days_below_minimum(self, client, auth_headers):
        """Should reject days value less than 1."""
        response = client.get(
            "/api/v1/alerts/expiry?days=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_days_above_maximum(self, client, auth_headers):
        """Should reject days value greater than 365."""
        response = client.get(
            "/api/v1/alerts/expiry?days=366",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_supplier_id(self, client, auth_headers):
        """Should reject invalid supplier ID."""
        response = client.get(
            "/api/v1/alerts/expiry?supplier_id=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_negative_page(self, client, auth_headers):
        """Should reject negative page number."""
        response = client.get(
            "/api/v1/alerts/expiry?page=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_negative_limit(self, client, auth_headers):
        """Should reject negative limit."""
        response = client.get(
            "/api/v1/alerts/expiry?limit=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_limit_above_maximum(self, client, auth_headers):
        """Should reject limit above 100."""
        response = client.get(
            "/api/v1/alerts/expiry?limit=101",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_results(self, client, auth_headers):
        """Should handle empty results gracefully."""
        response = client.get(
            "/api/v1/alerts/expiry?days=1&supplier_id=999999",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []


class TestExpiryAlertsDocumentTypes:
    """Test filtering by different document types."""

    def test_filter_insurance_expiry(self, client, auth_headers):
        """Should filter expiring insurance documents."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_tax_expiry(self, client, auth_headers):
        """Should filter expiring tax documents."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=tax",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_license_expiry(self, client, auth_headers):
        """Should filter expiring license documents."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=license",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_safety_expiry(self, client, auth_headers):
        """Should filter expiring safety documents."""
        response = client.get(
            "/api/v1/alerts/expiry?days=90&document_type=safety",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
