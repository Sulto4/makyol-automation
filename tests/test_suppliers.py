"""
Suppliers API Endpoint Tests

Tests for suppliers endpoints including:
- List suppliers with filtering and pagination
- Get supplier by ID
- Filtering by category, active status, and search
- Pagination validation
- Error handling (not found, invalid parameters)
"""

import pytest
from fastapi import status


class TestListSuppliers:
    """Test GET /api/v1/suppliers endpoint."""

    def test_list_suppliers_basic(self, client, auth_headers):
        """Should return paginated list of suppliers."""
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert isinstance(data["data"], list)
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_suppliers_custom_pagination(self, client, auth_headers):
        """Should support custom page and limit parameters."""
        response = client.get(
            "/api/v1/suppliers?page=1&limit=2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["data"]) <= 2

    def test_list_suppliers_filter_by_category(self, client, auth_headers):
        """Should filter suppliers by category."""
        response = client.get(
            "/api/v1/suppliers?category=construction",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["category"] == "construction"

    def test_list_suppliers_filter_by_active_status(self, client, auth_headers):
        """Should filter suppliers by active status."""
        response = client.get(
            "/api/v1/suppliers?is_active=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["is_active"] is True

    def test_list_suppliers_filter_inactive(self, client, auth_headers):
        """Should filter inactive suppliers."""
        response = client.get(
            "/api/v1/suppliers?is_active=false",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] >= 1
        for supplier in data["data"]:
            assert supplier["is_active"] is False

    def test_list_suppliers_search(self, client, auth_headers):
        """Should search suppliers by name."""
        response = client.get(
            "/api/v1/suppliers?search=ABC",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] >= 1
        # Verify search matches name
        for supplier in data["data"]:
            assert (
                "abc" in supplier["name"].lower() or
                "abc" in (supplier["registration_number"] or "").lower() or
                "abc" in (supplier["contact_person"] or "").lower()
            )

    def test_list_suppliers_combined_filters(self, client, auth_headers):
        """Should support multiple filters simultaneously."""
        response = client.get(
            "/api/v1/suppliers?category=construction&is_active=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["category"] == "construction"
            assert supplier["is_active"] is True

    def test_list_suppliers_pagination_navigation(self, client, auth_headers):
        """Should provide correct pagination navigation."""
        response = client.get(
            "/api/v1/suppliers?page=1&limit=2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["has_previous"] is False
        if data["total"] > 2:
            assert data["has_next"] is True
            assert data["next_page"] == 2
        assert data["previous_page"] is None

    def test_list_suppliers_invalid_page(self, client, auth_headers):
        """Should return 404 for invalid page number."""
        response = client.get(
            "/api/v1/suppliers?page=999",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data or "message" in data

    def test_list_suppliers_response_structure(self, client, auth_headers):
        """Should return suppliers with correct structure."""
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if len(data["data"]) > 0:
            supplier = data["data"][0]
            assert "id" in supplier
            assert "name" in supplier
            assert "registration_number" in supplier
            assert "category" in supplier
            assert "email" in supplier
            assert "phone" in supplier
            assert "is_active" in supplier
            assert "created_at" in supplier
            assert "updated_at" in supplier


class TestGetSupplierById:
    """Test GET /api/v1/suppliers/{id} endpoint."""

    def test_get_supplier_success(self, client, auth_headers):
        """Should return supplier details for valid ID."""
        response = client.get("/api/v1/suppliers/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        supplier = response.json()
        assert supplier["id"] == 1
        assert "name" in supplier
        assert "registration_number" in supplier
        assert "category" in supplier

    def test_get_supplier_not_found(self, client, auth_headers):
        """Should return 404 for non-existent supplier."""
        response = client.get("/api/v1/suppliers/999999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = data.get("error") or data.get("message")
        assert "999999" in error_msg

    def test_get_supplier_response_structure(self, client, auth_headers):
        """Should return complete supplier information."""
        response = client.get("/api/v1/suppliers/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        supplier = response.json()
        assert isinstance(supplier["id"], int)
        assert isinstance(supplier["name"], str)
        assert isinstance(supplier["is_active"], bool)
        assert supplier["category"] in [
            "construction", "equipment", "consulting", "labor", "other"
        ]

    def test_get_supplier_multiple_ids(self, client, auth_headers):
        """Should retrieve different suppliers by ID."""
        response1 = client.get("/api/v1/suppliers/1", headers=auth_headers)
        response2 = client.get("/api/v1/suppliers/2", headers=auth_headers)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        supplier1 = response1.json()
        supplier2 = response2.json()

        assert supplier1["id"] == 1
        assert supplier2["id"] == 2
        assert supplier1["name"] != supplier2["name"]


class TestSuppliersAuthentication:
    """Test authentication requirements for suppliers endpoints."""

    def test_list_suppliers_requires_auth(self, client):
        """List suppliers should require authentication."""
        response = client.get("/api/v1/suppliers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_supplier_requires_auth(self, client):
        """Get supplier by ID should require authentication."""
        response = client.get("/api/v1/suppliers/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_suppliers_with_invalid_api_key(self, client, invalid_auth_headers):
        """Suppliers endpoints should reject invalid API key."""
        response = client.get("/api/v1/suppliers", headers=invalid_auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSuppliersEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_list_suppliers_max_limit(self, client, auth_headers):
        """Should respect maximum limit of 100."""
        response = client.get(
            "/api/v1/suppliers?limit=100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page_size"] == 100

    def test_list_suppliers_empty_search(self, client, auth_headers):
        """Should return all suppliers when search matches nothing."""
        response = client.get(
            "/api/v1/suppliers?search=NONEXISTENTSUPPLIER12345",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    def test_list_suppliers_page_zero(self, client, auth_headers):
        """Should reject page number less than 1."""
        response = client.get(
            "/api/v1/suppliers?page=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_suppliers_negative_limit(self, client, auth_headers):
        """Should reject negative limit."""
        response = client.get(
            "/api/v1/suppliers?limit=-1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_supplier_invalid_id(self, client, auth_headers):
        """Should reject invalid supplier ID."""
        response = client.get("/api/v1/suppliers/0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
