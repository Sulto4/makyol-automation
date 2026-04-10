"""
Authentication Middleware Tests

Tests for API key authentication middleware including:
- Valid API key acceptance
- Invalid API key rejection
- Missing API key rejection
- Public endpoint access
- Protected endpoint access
"""

import pytest
from fastapi import status


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""

    def test_health_endpoint_no_auth(self, client):
        """Health endpoint should be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"

    def test_root_endpoint_no_auth(self, client):
        """Root endpoint should be accessible without authentication."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

    def test_docs_endpoint_no_auth(self, client):
        """Swagger docs should be accessible without authentication."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_redoc_endpoint_no_auth(self, client):
        """ReDoc should be accessible without authentication."""
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_json_no_auth(self, client):
        """OpenAPI JSON should be accessible without authentication."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        assert "openapi" in response.json()


class TestAuthenticationRequired:
    """Test that protected endpoints require authentication."""

    def test_protected_endpoint_without_api_key(self, client):
        """Protected endpoint should reject requests without API key."""
        response = client.get("/api/v1/test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()
        assert response.json()["detail"] == "Invalid or missing API key"

    def test_protected_endpoint_with_invalid_api_key(self, client, invalid_auth_headers):
        """Protected endpoint should reject requests with invalid API key."""
        response = client.get("/api/v1/test", headers=invalid_auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid or missing API key"

    def test_protected_endpoint_with_empty_api_key(self, client):
        """Protected endpoint should reject requests with empty API key."""
        headers = {"X-API-Key": ""}
        response = client.get("/api/v1/test", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_suppliers_endpoint_without_auth(self, client):
        """Suppliers endpoint should require authentication."""
        response = client.get("/api/v1/suppliers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_documents_endpoint_without_auth(self, client):
        """Documents endpoint should require authentication."""
        response = client.get("/api/v1/documents")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_compliance_endpoint_without_auth(self, client):
        """Compliance endpoint should require authentication."""
        response = client.get("/api/v1/compliance/suppliers/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_alerts_endpoint_without_auth(self, client):
        """Alerts endpoint should require authentication."""
        response = client.get("/api/v1/alerts/expiry")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reports_endpoint_without_auth(self, client):
        """Reports endpoint should require authentication."""
        response = client.get("/api/v1/reports/compliance")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestValidAuthentication:
    """Test that valid API keys grant access to protected endpoints."""

    def test_test_endpoint_with_valid_api_key(self, client, auth_headers):
        """Test endpoint should accept valid API key."""
        response = client.get("/api/v1/test", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

    def test_suppliers_endpoint_with_valid_api_key(self, client, auth_headers):
        """Suppliers endpoint should accept valid API key."""
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_documents_endpoint_with_valid_api_key(self, client, auth_headers):
        """Documents endpoint should accept valid API key."""
        response = client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_compliance_endpoint_with_valid_api_key(self, client, auth_headers):
        """Compliance endpoint should accept valid API key."""
        response = client.get("/api/v1/compliance/suppliers/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_alerts_endpoint_with_valid_api_key(self, client, auth_headers):
        """Alerts endpoint should accept valid API key."""
        response = client.get("/api/v1/alerts/expiry", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_reports_endpoint_with_valid_api_key(self, client, auth_headers):
        """Reports endpoint should accept valid API key."""
        response = client.get("/api/v1/reports/compliance", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestAuthenticationErrorResponse:
    """Test that authentication errors return proper error responses."""

    def test_unauthorized_error_structure(self, client):
        """Unauthorized errors should have consistent structure."""
        response = client.get("/api/v1/test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "detail" in data
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Unauthorized"

    def test_unauthorized_error_message(self, client):
        """Unauthorized errors should provide helpful message."""
        response = client.get("/api/v1/test")
        data = response.json()

        assert "API key" in data["message"] or "API key" in data["detail"]
        assert "X-API-Key" in data["message"]

    def test_invalid_key_error_structure(self, client, invalid_auth_headers):
        """Invalid API key errors should have consistent structure."""
        response = client.get("/api/v1/test", headers=invalid_auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "detail" in data
        assert "error" in data
        assert data["error"] == "Unauthorized"


class TestCORSPreflightRequests:
    """Test that OPTIONS requests bypass authentication (CORS preflight)."""

    def test_options_request_without_auth(self, client):
        """OPTIONS requests should not require authentication."""
        response = client.options("/api/v1/suppliers")
        # OPTIONS should either succeed or return 405 (Method Not Allowed),
        # but not 401 (Unauthorized)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
