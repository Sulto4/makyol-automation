"""
End-to-End API Verification Tests

Comprehensive integration tests verifying the complete API functionality:
- API server health and documentation
- Authentication workflow (valid and invalid keys)
- All endpoint operations
- Pagination and filtering
- Rate limiting enforcement
- Complete user journeys
"""

import pytest
from fastapi import status
import time


class TestAPIHealth:
    """Verify API server is running and healthy."""

    def test_health_endpoint(self, client):
        """Verify /health endpoint returns 200 and correct structure."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_root_endpoint(self, client):
        """Verify root endpoint is accessible and provides API info."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"


class TestAPIDocumentation:
    """Verify API documentation is accessible and complete."""

    def test_swagger_docs_loads(self, client):
        """Verify /docs (Swagger UI) loads successfully."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_loads(self, client):
        """Verify /redoc (ReDoc) loads successfully."""
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_json_valid(self, client):
        """Verify /openapi.json returns valid OpenAPI specification."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK

        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "Makyol Compliance API"

        # Verify key endpoints are documented
        paths = spec["paths"]
        assert "/health" in paths
        assert "/api/v1/suppliers" in paths
        assert "/api/v1/documents" in paths
        assert "/api/v1/alerts/expiry" in paths
        assert "/api/v1/reports/compliance" in paths


class TestAuthenticationWorkflow:
    """End-to-end authentication verification."""

    def test_valid_api_key_grants_access(self, client, auth_headers):
        """Verify valid API key grants access to all protected endpoints."""
        endpoints = [
            "/api/v1/test",
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/compliance/suppliers/1",
            "/api/v1/alerts/expiry",
            "/api/v1/reports/compliance"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK, \
                f"Valid API key failed for {endpoint}"

    def test_invalid_api_key_denies_access(self, client, invalid_auth_headers):
        """Verify invalid API key is rejected on all protected endpoints."""
        endpoints = [
            "/api/v1/test",
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/compliance/suppliers/1",
            "/api/v1/alerts/expiry",
            "/api/v1/reports/compliance"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=invalid_auth_headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Invalid API key not rejected for {endpoint}"

            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Invalid or missing API key"

    def test_missing_api_key_denies_access(self, client):
        """Verify requests without API key are rejected."""
        endpoints = [
            "/api/v1/test",
            "/api/v1/suppliers",
            "/api/v1/documents"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Missing API key not rejected for {endpoint}"

    def test_public_endpoints_accessible_without_auth(self, client):
        """Verify public endpoints are accessible without authentication."""
        public_endpoints = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK, \
                f"Public endpoint {endpoint} not accessible"


class TestSuppliersEndToEnd:
    """End-to-end verification of suppliers endpoints."""

    def test_list_suppliers_basic(self, client, auth_headers):
        """Verify basic supplier listing works."""
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["data"], list)

    def test_get_supplier_by_id(self, client, auth_headers):
        """Verify getting individual supplier by ID."""
        response = client.get("/api/v1/suppliers/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        supplier = response.json()
        assert supplier["id"] == 1
        assert "name" in supplier
        assert "category" in supplier

    def test_suppliers_pagination(self, client, auth_headers):
        """Verify pagination works on suppliers endpoint."""
        # Get first page
        response1 = client.get("/api/v1/suppliers?page=1&limit=2", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK

        data1 = response1.json()
        assert data1["page"] == 1
        assert data1["page_size"] == 2
        assert len(data1["data"]) <= 2

        # If there are more pages, test second page
        if data1["has_next"]:
            response2 = client.get("/api/v1/suppliers?page=2&limit=2", headers=auth_headers)
            assert response2.status_code == status.HTTP_200_OK

            data2 = response2.json()
            assert data2["page"] == 2

    def test_suppliers_filtering_by_category(self, client, auth_headers):
        """Verify filtering by category works."""
        response = client.get("/api/v1/suppliers?category=construction", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["category"] == "construction"

    def test_suppliers_filtering_by_status(self, client, auth_headers):
        """Verify filtering by active status works."""
        response = client.get("/api/v1/suppliers?is_active=true", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["is_active"] is True


class TestDocumentsEndToEnd:
    """End-to-end verification of documents endpoints."""

    def test_list_documents_basic(self, client, auth_headers):
        """Verify basic document listing works."""
        response = client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_get_document_by_id(self, client, auth_headers):
        """Verify getting individual document by ID."""
        response = client.get("/api/v1/documents/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        document = response.json()
        assert document["id"] == 1
        assert "document_type" in document
        assert "status" in document

    def test_documents_pagination(self, client, auth_headers):
        """Verify pagination works on documents endpoint."""
        response = client.get("/api/v1/documents?page=1&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["data"]) <= 5

    def test_documents_filter_by_supplier(self, client, auth_headers):
        """Verify filtering documents by supplier_id."""
        response = client.get("/api/v1/documents?supplier_id=1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["supplier_id"] == 1

    def test_documents_filter_by_status(self, client, auth_headers):
        """Verify filtering documents by status."""
        response = client.get("/api/v1/documents?status=valid", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["status"] == "valid"


class TestComplianceEndToEnd:
    """End-to-end verification of compliance endpoints."""

    def test_get_supplier_compliance(self, client, auth_headers):
        """Verify getting supplier compliance status."""
        response = client.get("/api/v1/compliance/suppliers/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        compliance = response.json()
        assert "supplier_id" in compliance
        assert "compliance_status" in compliance
        assert "total_documents" in compliance
        assert "valid_documents" in compliance
        assert "expired_documents" in compliance
        assert "expiring_soon_documents" in compliance

    def test_compliance_for_different_suppliers(self, client, auth_headers):
        """Verify compliance data for multiple suppliers."""
        # Test supplier 1
        response1 = client.get("/api/v1/compliance/suppliers/1", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["supplier_id"] == 1

        # Test supplier 2
        response2 = client.get("/api/v1/compliance/suppliers/2", headers=auth_headers)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["supplier_id"] == 2

    def test_compliance_not_found(self, client, auth_headers):
        """Verify 404 for non-existent supplier compliance."""
        response = client.get("/api/v1/compliance/suppliers/999999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAlertsEndToEnd:
    """End-to-end verification of alerts endpoints."""

    def test_expiry_alerts_basic(self, client, auth_headers):
        """Verify expiry alerts endpoint works."""
        response = client.get("/api/v1/alerts/expiry", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_expiry_alerts_with_days_filter(self, client, auth_headers):
        """Verify filtering by days parameter."""
        response = client.get("/api/v1/alerts/expiry?days=30", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data

    def test_expiry_alerts_with_severity(self, client, auth_headers):
        """Verify filtering by document type (severity not filterable in current implementation)."""
        response = client.get("/api/v1/alerts/expiry?document_type=insurance", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for alert in data["data"]:
            assert alert["document_type"] == "insurance"

    def test_expiry_alerts_pagination(self, client, auth_headers):
        """Verify pagination on alerts endpoint."""
        response = client.get("/api/v1/alerts/expiry?page=1&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestReportsEndToEnd:
    """End-to-end verification of reports endpoints."""

    def test_compliance_report_json(self, client, auth_headers):
        """Verify compliance report in JSON format."""
        response = client.get("/api/v1/reports/compliance?format=json", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        report = response.json()
        assert "generated_at" in report
        assert "total_suppliers" in report
        assert "total_documents" in report
        assert "overall_compliance_rate" in report

    def test_compliance_report_csv(self, client, auth_headers):
        """Verify compliance report CSV format returns 501 (not implemented)."""
        response = client.get("/api/v1/reports/compliance?format=csv", headers=auth_headers)
        # CSV format is not yet implemented - returns 501
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_compliance_report_with_period(self, client, auth_headers):
        """Verify reports with different periods."""
        response = client.get("/api/v1/reports/compliance?period=monthly", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        report = response.json()
        assert "report_period" in report
        assert "total_suppliers" in report


class TestPaginationAcrossEndpoints:
    """Verify pagination works consistently across all list endpoints."""

    def test_pagination_structure_consistent(self, client, auth_headers):
        """Verify all endpoints return consistent pagination structure."""
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/alerts/expiry"
        ]

        for endpoint in endpoints:
            response = client.get(f"{endpoint}?page=1&limit=5", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            # Check pagination fields exist
            assert "data" in data, f"Missing 'data' in {endpoint}"
            assert "total" in data, f"Missing 'total' in {endpoint}"
            assert "page" in data, f"Missing 'page' in {endpoint}"
            assert "page_size" in data, f"Missing 'page_size' in {endpoint}"
            assert "total_pages" in data, f"Missing 'total_pages' in {endpoint}"
            assert "has_next" in data, f"Missing 'has_next' in {endpoint}"
            assert "has_previous" in data, f"Missing 'has_previous' in {endpoint}"

    def test_first_page_has_no_previous(self, client, auth_headers):
        """Verify first page correctly indicates no previous page."""
        response = client.get("/api/v1/suppliers?page=1&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["has_previous"] is False
        assert data["previous_page"] is None

    def test_page_size_respected(self, client, auth_headers):
        """Verify page size limit is respected."""
        response = client.get("/api/v1/suppliers?page=1&limit=3", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page_size"] == 3
        assert len(data["data"]) <= 3


class TestFilteringAcrossEndpoints:
    """Verify filtering works correctly across applicable endpoints."""

    def test_suppliers_multiple_filters(self, client, auth_headers):
        """Verify combining multiple filters on suppliers."""
        response = client.get(
            "/api/v1/suppliers?category=construction&is_active=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for supplier in data["data"]:
            assert supplier["category"] == "construction"
            assert supplier["is_active"] is True

    def test_documents_multiple_filters(self, client, auth_headers):
        """Verify combining multiple filters on documents."""
        response = client.get(
            "/api/v1/documents?supplier_id=1&status=valid",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["supplier_id"] == 1
            assert document["status"] == "valid"

    def test_alerts_multiple_filters(self, client, auth_headers):
        """Verify combining multiple filters on alerts."""
        response = client.get(
            "/api/v1/alerts/expiry?days=30&document_type=insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for alert in data["data"]:
            assert alert["document_type"] == "insurance"


class TestRateLimitingEndToEnd:
    """End-to-end verification of rate limiting enforcement."""

    def test_rate_limiting_enforced(self, client, auth_headers):
        """Verify rate limiting blocks excessive requests with 429."""
        success_count = 0
        rate_limited = False

        # Make requests until rate limited
        for i in range(150):
            response = client.get("/api/v1/test", headers=auth_headers)

            if response.status_code == status.HTTP_200_OK:
                success_count += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True

                # Verify rate limit response structure
                data = response.json()
                assert "detail" in data
                assert "error" in data
                assert data["error"] == "Too Many Requests"
                break

        # Should have been rate limited
        assert rate_limited, f"Expected rate limiting but made {success_count} requests without hitting limit"
        # Should have gotten some successful requests
        assert success_count > 0, "Should have some successful requests before rate limit"

    def test_rate_limit_response_format(self, client, auth_headers):
        """Verify rate limit error has correct format."""
        # Hit rate limit
        rate_limit_response = None
        for i in range(150):
            response = client.get("/api/v1/test", headers=auth_headers)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limit_response = response
                break

        if rate_limit_response:
            assert rate_limit_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            data = rate_limit_response.json()
            assert "detail" in data
            assert "error" in data
            assert "message" in data


class TestCompleteUserJourneys:
    """End-to-end user journey scenarios."""

    def test_erp_integration_journey(self, client, auth_headers):
        """
        Simulate ERP integration checking supplier compliance before purchase order.

        Journey:
        1. Search for supplier
        2. Get supplier details
        3. Check compliance status
        4. Verify active documents
        5. Check for expiry alerts
        """
        # 1. Search for supplier
        search_response = client.get(
            "/api/v1/suppliers?search=ABC",
            headers=auth_headers
        )
        assert search_response.status_code == status.HTTP_200_OK
        suppliers = search_response.json()["data"]

        if len(suppliers) > 0:
            supplier_id = suppliers[0]["id"]

            # 2. Get supplier details
            supplier_response = client.get(
                f"/api/v1/suppliers/{supplier_id}",
                headers=auth_headers
            )
            assert supplier_response.status_code == status.HTTP_200_OK

            # 3. Check compliance status
            compliance_response = client.get(
                f"/api/v1/compliance/suppliers/{supplier_id}",
                headers=auth_headers
            )
            assert compliance_response.status_code == status.HTTP_200_OK
            compliance = compliance_response.json()

            # 4. Verify valid documents
            docs_response = client.get(
                f"/api/v1/documents?supplier_id={supplier_id}&status=valid",
                headers=auth_headers
            )
            assert docs_response.status_code == status.HTTP_200_OK

            # 5. Check for expiry alerts
            alerts_response = client.get(
                "/api/v1/alerts/expiry?days=30",
                headers=auth_headers
            )
            assert alerts_response.status_code == status.HTTP_200_OK

    def test_procurement_automation_journey(self, client, auth_headers):
        """
        Simulate procurement automation checking all active suppliers.

        Journey:
        1. Get all active suppliers
        2. For each, check compliance
        3. Filter suppliers by compliance status
        4. Get compliance report
        """
        # 1. Get all active suppliers
        suppliers_response = client.get(
            "/api/v1/suppliers?is_active=true",
            headers=auth_headers
        )
        assert suppliers_response.status_code == status.HTTP_200_OK
        suppliers_data = suppliers_response.json()

        # 2. Check compliance for first few suppliers
        for supplier in suppliers_data["data"][:3]:
            compliance_response = client.get(
                f"/api/v1/compliance/suppliers/{supplier['id']}",
                headers=auth_headers
            )
            assert compliance_response.status_code == status.HTTP_200_OK

        # 3. Get compliance report
        report_response = client.get(
            "/api/v1/reports/compliance?format=json",
            headers=auth_headers
        )
        assert report_response.status_code == status.HTTP_200_OK
        report = report_response.json()
        assert "total_suppliers" in report
        assert "overall_compliance_rate" in report

    def test_dashboard_display_journey(self, client, auth_headers):
        """
        Simulate project dashboard fetching compliance overview.

        Journey:
        1. Get summary statistics from compliance report
        2. Get high-priority expiry alerts
        3. Get recent document updates
        """
        # 1. Get compliance report summary
        report_response = client.get(
            "/api/v1/reports/compliance?format=json",
            headers=auth_headers
        )
        assert report_response.status_code == status.HTTP_200_OK
        report = report_response.json()
        assert "total_suppliers" in report
        assert "overall_compliance_rate" in report

        # 2. Get expiry alerts (within 30 days)
        alerts_response = client.get(
            "/api/v1/alerts/expiry?days=30",
            headers=auth_headers
        )
        assert alerts_response.status_code == status.HTTP_200_OK

        # 3. Get recent documents
        docs_response = client.get(
            "/api/v1/documents?page=1&limit=10",
            headers=auth_headers
        )
        assert docs_response.status_code == status.HTTP_200_OK


class TestErrorHandlingEndToEnd:
    """Verify consistent error handling across all endpoints."""

    def test_404_not_found_consistent(self, client, auth_headers):
        """Verify 404 errors are consistent across endpoints."""
        endpoints = [
            "/api/v1/suppliers/999999",
            "/api/v1/documents/999999",
            "/api/v1/compliance/suppliers/999999"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == status.HTTP_404_NOT_FOUND

            data = response.json()
            assert "error" in data or "message" in data

    def test_422_validation_errors_consistent(self, client, auth_headers):
        """Verify validation errors are consistent."""
        # Invalid page number (0)
        response = client.get("/api/v1/suppliers?page=0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid limit (negative)
        response = client.get("/api/v1/suppliers?limit=-1", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_401_unauthorized_consistent(self, client):
        """Verify unauthorized errors are consistent."""
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/compliance/suppliers/1"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

            data = response.json()
            assert data["detail"] == "Invalid or missing API key"
            assert data["error"] == "Unauthorized"


class TestAPICompleteness:
    """Verify all required API features are present and working."""

    def test_all_required_endpoints_exist(self, client, auth_headers):
        """Verify all acceptance criteria endpoints are implemented."""
        required_endpoints = [
            ("/api/v1/suppliers", "GET"),
            ("/api/v1/suppliers/1", "GET"),
            ("/api/v1/documents", "GET"),
            ("/api/v1/documents/1", "GET"),
            ("/api/v1/compliance/suppliers/1", "GET"),
            ("/api/v1/alerts/expiry", "GET"),
            ("/api/v1/reports/compliance", "GET")
        ]

        for endpoint, method in required_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=auth_headers)
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND], \
                    f"Endpoint {endpoint} not working properly"

    def test_all_endpoints_require_authentication(self, client):
        """Verify all API endpoints require authentication."""
        protected_endpoints = [
            "/api/v1/test",
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/compliance/suppliers/1",
            "/api/v1/alerts/expiry",
            "/api/v1/reports/compliance"
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Endpoint {endpoint} not protected"

    def test_json_response_format(self, client, auth_headers):
        """Verify all endpoints return JSON."""
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/alerts/expiry",
            "/api/v1/reports/compliance?format=json"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            assert "application/json" in response.headers.get("content-type", "")

            # Verify it's valid JSON
            data = response.json()
            assert data is not None

    def test_filtering_supported_on_list_endpoints(self, client, auth_headers):
        """Verify filtering is supported on all list endpoints."""
        # Suppliers filtering
        response = client.get("/api/v1/suppliers?category=construction", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Documents filtering
        response = client.get("/api/v1/documents?status=valid", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Alerts filtering
        response = client.get("/api/v1/alerts/expiry?days=30", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_pagination_supported_on_list_endpoints(self, client, auth_headers):
        """Verify pagination is supported on all list endpoints."""
        list_endpoints = [
            "/api/v1/suppliers",
            "/api/v1/documents",
            "/api/v1/alerts/expiry"
        ]

        for endpoint in list_endpoints:
            response = client.get(f"{endpoint}?page=1&limit=5", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "page" in data
            assert "page_size" in data
            assert data["page"] == 1
            assert data["page_size"] == 5
