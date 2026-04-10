"""
Documents API Endpoint Tests

Tests for documents endpoints including:
- List documents with filtering and pagination
- Get document by ID
- Filtering by supplier, document type, status, required flag
- Search functionality
- Error handling and validation
"""

import pytest
from fastapi import status


class TestListDocuments:
    """Test GET /api/v1/documents endpoint."""

    def test_list_documents_basic(self, client, auth_headers):
        """Should return paginated list of documents."""
        response = client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["data"], list)

    def test_list_documents_custom_pagination(self, client, auth_headers):
        """Should support custom page and limit parameters."""
        response = client.get(
            "/api/v1/documents?page=1&limit=5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["data"]) <= 5

    def test_list_documents_filter_by_supplier(self, client, auth_headers):
        """Should filter documents by supplier ID."""
        response = client.get(
            "/api/v1/documents?supplier_id=1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["supplier_id"] == 1

    def test_list_documents_filter_by_type(self, client, auth_headers):
        """Should filter documents by document type."""
        response = client.get(
            "/api/v1/documents?document_type=insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["document_type"] == "insurance"

    def test_list_documents_filter_by_status(self, client, auth_headers):
        """Should filter documents by status."""
        response = client.get(
            "/api/v1/documents?status=valid",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["status"] == "valid"

    def test_list_documents_filter_required(self, client, auth_headers):
        """Should filter documents by required flag."""
        response = client.get(
            "/api/v1/documents?is_required=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["is_required"] is True

    def test_list_documents_search(self, client, auth_headers):
        """Should search documents by name and supplier."""
        response = client.get(
            "/api/v1/documents?search=Insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            search_text = "insurance"
            assert (
                search_text in document["document_name"].lower() or
                search_text in document["supplier_name"].lower() or
                (document.get("validation_notes") and
                 search_text in document["validation_notes"].lower())
            )

    def test_list_documents_combined_filters(self, client, auth_headers):
        """Should support multiple filters simultaneously."""
        response = client.get(
            "/api/v1/documents?supplier_id=1&status=valid&is_required=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["supplier_id"] == 1
            assert document["status"] == "valid"
            assert document["is_required"] is True

    def test_list_documents_expired_status(self, client, auth_headers):
        """Should filter expired documents."""
        response = client.get(
            "/api/v1/documents?status=expired",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for document in data["data"]:
            assert document["status"] == "expired"

    def test_list_documents_response_structure(self, client, auth_headers):
        """Should return documents with correct structure."""
        response = client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if len(data["data"]) > 0:
            document = data["data"][0]
            assert "id" in document
            assert "supplier_id" in document
            assert "supplier_name" in document
            assert "document_type" in document
            assert "document_name" in document
            assert "status" in document
            assert "is_required" in document
            assert "uploaded_at" in document


class TestGetDocumentById:
    """Test GET /api/v1/documents/{id} endpoint."""

    def test_get_document_success(self, client, auth_headers):
        """Should return document details for valid ID."""
        response = client.get("/api/v1/documents/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        document = response.json()
        assert document["id"] == 1
        assert "document_name" in document
        assert "supplier_name" in document
        assert "document_type" in document

    def test_get_document_not_found(self, client, auth_headers):
        """Should return 404 for non-existent document."""
        response = client.get("/api/v1/documents/999999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "error" in data or "message" in data
        error_msg = data.get("error") or data.get("message")
        assert "999999" in error_msg

    def test_get_document_response_structure(self, client, auth_headers):
        """Should return complete document information."""
        response = client.get("/api/v1/documents/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        document = response.json()
        assert isinstance(document["id"], int)
        assert isinstance(document["supplier_id"], int)
        assert isinstance(document["document_name"], str)
        assert isinstance(document["is_required"], bool)
        assert document["document_type"] in [
            "registration", "tax", "insurance", "license",
            "financial", "quality", "safety", "contract", "other"
        ]
        assert document["status"] in [
            "valid", "expired", "expiring_soon", "pending_review",
            "rejected", "archived"
        ]

    def test_get_document_with_file_info(self, client, auth_headers):
        """Should include file information in response."""
        response = client.get("/api/v1/documents/1", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        document = response.json()
        assert "file_path" in document
        assert "file_size" in document
        assert "mime_type" in document
        assert isinstance(document["file_size"], int)


class TestDocumentsAuthentication:
    """Test authentication requirements for documents endpoints."""

    def test_list_documents_requires_auth(self, client):
        """List documents should require authentication."""
        response = client.get("/api/v1/documents")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_document_requires_auth(self, client):
        """Get document by ID should require authentication."""
        response = client.get("/api/v1/documents/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_documents_with_invalid_api_key(self, client, invalid_auth_headers):
        """Documents endpoints should reject invalid API key."""
        response = client.get("/api/v1/documents", headers=invalid_auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDocumentsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_list_documents_invalid_page(self, client, auth_headers):
        """Should return 404 for invalid page number."""
        response = client.get(
            "/api/v1/documents?page=999",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_documents_empty_search(self, client, auth_headers):
        """Should return empty list when search matches nothing."""
        response = client.get(
            "/api/v1/documents?search=NONEXISTENTDOCUMENT12345",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    def test_list_documents_invalid_supplier_id(self, client, auth_headers):
        """Should reject invalid supplier ID."""
        response = client.get(
            "/api/v1/documents?supplier_id=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_documents_max_limit(self, client, auth_headers):
        """Should respect maximum limit of 100."""
        response = client.get(
            "/api/v1/documents?limit=100",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page_size"] == 100

    def test_get_document_invalid_id(self, client, auth_headers):
        """Should reject invalid document ID."""
        response = client.get("/api/v1/documents/0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_documents_filter_nonexistent_supplier(self, client, auth_headers):
        """Should return empty list for non-existent supplier."""
        response = client.get(
            "/api/v1/documents?supplier_id=999999",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] == 0


class TestDocumentTypes:
    """Test different document types."""

    def test_filter_insurance_documents(self, client, auth_headers):
        """Should filter insurance documents."""
        response = client.get(
            "/api/v1/documents?document_type=insurance",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_tax_documents(self, client, auth_headers):
        """Should filter tax documents."""
        response = client.get(
            "/api/v1/documents?document_type=tax",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_safety_documents(self, client, auth_headers):
        """Should filter safety documents."""
        response = client.get(
            "/api/v1/documents?document_type=safety",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestDocumentStatuses:
    """Test different document statuses."""

    def test_filter_expiring_soon_documents(self, client, auth_headers):
        """Should filter documents expiring soon."""
        response = client.get(
            "/api/v1/documents?status=expiring_soon",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_pending_review_documents(self, client, auth_headers):
        """Should filter documents pending review."""
        response = client.get(
            "/api/v1/documents?status=pending_review",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_archived_documents(self, client, auth_headers):
        """Should filter archived documents."""
        response = client.get(
            "/api/v1/documents?status=archived",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
