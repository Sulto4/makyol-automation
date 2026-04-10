# API Documentation

Complete REST API reference for the PDF Text Extraction Engine.

## Base URL

```
http://localhost:3000/api
```

In production, replace with your domain:
```
https://yourdomain.com/api
```

## Authentication

Currently, the API does not require authentication. In production, implement authentication middleware as needed.

## Content Types

All requests accept and return JSON, except file uploads which use `multipart/form-data`.

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "name": "ErrorType",
    "message": "Human-readable error message",
    "code": "ERROR_CODE"
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity (processing failed)
- `500` - Internal Server Error

## Endpoints

### Upload Document

Upload and process a PDF document.

**Endpoint**: `POST /api/documents`

**Request**:

Using `multipart/form-data`:

```bash
curl -X POST http://localhost:3000/api/documents \
  -F "file=@certificate.pdf"
```

Using file path (testing only):

```bash
curl -X POST http://localhost:3000/api/documents \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/absolute/path/to/certificate.pdf"}'
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes* | PDF file to upload (multipart/form-data) |
| `file_path` | String | Yes* | Absolute path to PDF file (testing only) |

*Either `file` or `file_path` must be provided

**Success Response** (201 Created):

```json
{
  "document": {
    "id": 1,
    "filename": "certificate.pdf",
    "original_filename": "ISO-9001-Certificate.pdf",
    "file_path": "/app/uploads/certificate.pdf",
    "file_size": 45678,
    "mime_type": "application/pdf",
    "processing_status": "completed",
    "error_message": null,
    "uploaded_at": "2026-04-11T10:30:00.000Z",
    "processing_started_at": "2026-04-11T10:30:00.100Z",
    "processing_completed_at": "2026-04-11T10:30:01.500Z",
    "created_at": "2026-04-11T10:30:00.000Z",
    "updated_at": "2026-04-11T10:30:01.500Z"
  },
  "extraction": {
    "id": 1,
    "document_id": 1,
    "extracted_text": "CERTIFICAT DE CONFORMITATE\nNr. ISO 9001:2015...",
    "metadata": {
      "certificate_number": "ISO 9001:2015",
      "certificate_number_confidence": 0.95,
      "issuing_organization": "SRAC - Asociația de Certificare Română",
      "issuing_organization_confidence": 1.0,
      "issue_date": "2024-01-15",
      "issue_date_confidence": 0.9,
      "expiry_date": "2027-01-15",
      "expiry_date_confidence": 0.9,
      "certified_company": "ACME Corporation SRL",
      "certified_company_confidence": 0.85,
      "certification_scope": "Sistem de Management al Calității conform ISO 9001:2015",
      "certification_scope_confidence": 0.8
    },
    "confidence_score": 0.88,
    "extraction_status": "success",
    "error_details": null,
    "created_at": "2026-04-11T10:30:01.000Z",
    "updated_at": "2026-04-11T10:30:01.000Z"
  }
}
```

**Error Responses**:

No file provided (400):
```json
{
  "error": {
    "name": "ValidationError",
    "message": "No file provided. Include a file upload or file_path in request body",
    "code": "NO_FILE_PROVIDED"
  }
}
```

Invalid file type (400):
```json
{
  "error": {
    "name": "ValidationError",
    "message": "Only PDF files are supported",
    "code": "INVALID_FILE_TYPE"
  }
}
```

File not found (400):
```json
{
  "error": {
    "name": "ValidationError",
    "message": "File not found at the specified path",
    "code": "FILE_NOT_FOUND"
  }
}
```

### List Documents

Retrieve a list of documents with optional filtering and pagination.

**Endpoint**: `GET /api/documents`

**Request**:

```bash
# Get all documents
curl http://localhost:3000/api/documents

# With pagination
curl http://localhost:3000/api/documents?limit=10&offset=20

# Filter by status
curl http://localhost:3000/api/documents?status=completed

# Combined
curl http://localhost:3000/api/documents?status=completed&limit=50&offset=0
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | Integer | No | Maximum number of documents to return |
| `offset` | Integer | No | Number of documents to skip (default: 0) |
| `status` | String | No | Filter by processing status: `pending`, `processing`, `completed`, `failed` |

**Success Response** (200 OK):

```json
{
  "documents": [
    {
      "id": 1,
      "filename": "certificate.pdf",
      "original_filename": "ISO-9001-Certificate.pdf",
      "file_path": "/app/uploads/certificate.pdf",
      "file_size": 45678,
      "mime_type": "application/pdf",
      "processing_status": "completed",
      "error_message": null,
      "uploaded_at": "2026-04-11T10:30:00.000Z",
      "processing_started_at": "2026-04-11T10:30:00.100Z",
      "processing_completed_at": "2026-04-11T10:30:01.500Z",
      "created_at": "2026-04-11T10:30:00.000Z",
      "updated_at": "2026-04-11T10:30:01.500Z"
    },
    {
      "id": 2,
      "filename": "cert-2.pdf",
      "original_filename": "Certificate-2.pdf",
      "file_path": "/app/uploads/cert-2.pdf",
      "file_size": 38902,
      "mime_type": "application/pdf",
      "processing_status": "completed",
      "error_message": null,
      "uploaded_at": "2026-04-11T11:15:00.000Z",
      "processing_started_at": "2026-04-11T11:15:00.050Z",
      "processing_completed_at": "2026-04-11T11:15:01.200Z",
      "created_at": "2026-04-11T11:15:00.000Z",
      "updated_at": "2026-04-11T11:15:01.200Z"
    }
  ],
  "count": 2,
  "limit": null,
  "offset": 0
}
```

**Error Responses**:

Invalid status (400):
```json
{
  "error": {
    "name": "ValidationError",
    "message": "Invalid status. Must be one of: pending, processing, completed, failed",
    "code": "INVALID_STATUS"
  }
}
```

### Get Document by ID

Retrieve a specific document and its extraction results by ID.

**Endpoint**: `GET /api/documents/:id`

**Request**:

```bash
curl http://localhost:3000/api/documents/1
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | Integer | Yes | Document ID |

**Success Response** (200 OK):

```json
{
  "document": {
    "id": 1,
    "filename": "certificate.pdf",
    "original_filename": "ISO-9001-Certificate.pdf",
    "file_path": "/app/uploads/certificate.pdf",
    "file_size": 45678,
    "mime_type": "application/pdf",
    "processing_status": "completed",
    "error_message": null,
    "uploaded_at": "2026-04-11T10:30:00.000Z",
    "processing_started_at": "2026-04-11T10:30:00.100Z",
    "processing_completed_at": "2026-04-11T10:30:01.500Z",
    "created_at": "2026-04-11T10:30:00.000Z",
    "updated_at": "2026-04-11T10:30:01.500Z"
  },
  "extraction": {
    "id": 1,
    "document_id": 1,
    "extracted_text": "CERTIFICAT DE CONFORMITATE\n\nNr. Certificat: ISO 9001:2015\n...",
    "metadata": {
      "certificate_number": "ISO 9001:2015",
      "certificate_number_confidence": 0.95,
      "issuing_organization": "SRAC - Asociația de Certificare Română",
      "issuing_organization_confidence": 1.0,
      "issue_date": "2024-01-15",
      "issue_date_confidence": 0.9,
      "expiry_date": "2027-01-15",
      "expiry_date_confidence": 0.9,
      "certified_company": "ACME Corporation SRL",
      "certified_company_confidence": 0.85,
      "certification_scope": "Sistem de Management al Calității",
      "certification_scope_confidence": 0.8
    },
    "confidence_score": 0.88,
    "extraction_status": "success",
    "error_details": null,
    "created_at": "2026-04-11T10:30:01.000Z",
    "updated_at": "2026-04-11T10:30:01.000Z"
  }
}
```

**Error Responses**:

Invalid ID (400):
```json
{
  "error": {
    "name": "ValidationError",
    "message": "Invalid document ID. Must be a positive integer.",
    "code": "INVALID_DOCUMENT_ID"
  }
}
```

Document not found (404):
```json
{
  "error": {
    "name": "NotFoundError",
    "message": "Document not found",
    "code": "DOCUMENT_NOT_FOUND"
  }
}
```

## Data Models

### Document

Represents an uploaded PDF document.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique document identifier |
| `filename` | String | Filename on server |
| `original_filename` | String | Original upload filename |
| `file_path` | String | Full path to file on disk |
| `file_size` | Integer | File size in bytes |
| `mime_type` | String | MIME type (always "application/pdf") |
| `processing_status` | String | Status: `pending`, `processing`, `completed`, `failed` |
| `error_message` | String | Error message if processing failed |
| `uploaded_at` | DateTime | Upload timestamp |
| `processing_started_at` | DateTime | Processing start timestamp |
| `processing_completed_at` | DateTime | Processing completion timestamp |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update timestamp |

### Extraction Result

Represents the extracted text and metadata from a document.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique extraction result identifier |
| `document_id` | Integer | Foreign key to document |
| `extracted_text` | String | Full text content from PDF |
| `metadata` | Object | Parsed metadata fields (see below) |
| `confidence_score` | Decimal | Overall confidence (0.0 to 1.0) |
| `extraction_status` | String | Status: `pending`, `success`, `partial`, `failed` |
| `error_details` | Object | Error information if failed |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update timestamp |

### Metadata Object

JSONB object containing extracted certificate metadata:

```json
{
  "certificate_number": "ISO 9001:2015",
  "certificate_number_confidence": 0.95,
  "issuing_organization": "SRAC - Asociația de Certificare Română",
  "issuing_organization_confidence": 1.0,
  "issue_date": "2024-01-15",
  "issue_date_confidence": 0.9,
  "expiry_date": "2027-01-15",
  "expiry_date_confidence": 0.9,
  "certified_company": "ACME Corporation SRL",
  "certified_company_confidence": 0.85,
  "certification_scope": "Sistem de Management al Calității",
  "certification_scope_confidence": 0.8
}
```

**Metadata Fields**:

| Field | Type | Description | Confidence Field |
|-------|------|-------------|------------------|
| `certificate_number` | String | Certificate/standard number | `certificate_number_confidence` |
| `issuing_organization` | String | Certifying organization | `issuing_organization_confidence` |
| `issue_date` | String | Issue date (ISO 8601) | `issue_date_confidence` |
| `expiry_date` | String | Expiry date (ISO 8601) | `expiry_date_confidence` |
| `certified_company` | String | Company name | `certified_company_confidence` |
| `certification_scope` | String | Certification scope | `certification_scope_confidence` |

## Processing Statuses

### Document Processing Status

- **`pending`**: Document uploaded, not yet processed
- **`processing`**: PDF extraction in progress
- **`completed`**: Processing finished successfully
- **`failed`**: Processing failed with errors

### Extraction Status

- **`pending`**: Extraction not yet started
- **`success`**: High-quality extraction (confidence ≥ 0.8)
- **`partial`**: Some metadata extracted (confidence 0.5-0.79)
- **`failed`**: Extraction failed or very low confidence (< 0.5)

## Examples

### Upload and Process Certificate

```bash
#!/bin/bash

# Upload certificate
response=$(curl -X POST http://localhost:3000/api/documents \
  -F "file=@certificate.pdf" \
  -s)

# Extract document ID
doc_id=$(echo $response | jq -r '.document.id')

# Check extraction status
echo "Document ID: $doc_id"
echo $response | jq '.extraction.extraction_status'

# View metadata
echo $response | jq '.extraction.metadata'
```

### List All Completed Documents

```bash
curl "http://localhost:3000/api/documents?status=completed" | jq '.'
```

### Get Document with Metadata

```bash
#!/bin/bash

doc_id=1

# Get document and extraction
curl "http://localhost:3000/api/documents/$doc_id" | jq '{
  filename: .document.original_filename,
  status: .extraction.extraction_status,
  confidence: .extraction.confidence_score,
  certificate_number: .extraction.metadata.certificate_number,
  issue_date: .extraction.metadata.issue_date,
  expiry_date: .extraction.metadata.expiry_date,
  company: .extraction.metadata.certified_company
}'
```

### Process Multiple PDFs

```bash
#!/bin/bash

for pdf in *.pdf; do
  echo "Processing $pdf..."
  
  result=$(curl -X POST http://localhost:3000/api/documents \
    -F "file=@$pdf" \
    -s)
  
  status=$(echo $result | jq -r '.extraction.extraction_status')
  confidence=$(echo $result | jq -r '.extraction.confidence_score')
  
  echo "  Status: $status (confidence: $confidence)"
done
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

async function uploadPDF(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));

  const response = await fetch('http://localhost:3000/api/documents', {
    method: 'POST',
    body: form,
  });

  const data = await response.json();
  
  if (response.ok) {
    console.log('Upload successful:', {
      id: data.document.id,
      status: data.extraction.extraction_status,
      confidence: data.extraction.confidence_score,
      metadata: data.extraction.metadata,
    });
  } else {
    console.error('Upload failed:', data.error);
  }
}

uploadPDF('./certificate.pdf');
```

### Python Example

```python
import requests

def upload_pdf(file_path):
    """Upload PDF and extract metadata"""
    
    url = 'http://localhost:3000/api/documents'
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 201:
        data = response.json()
        print(f"Document ID: {data['document']['id']}")
        print(f"Status: {data['extraction']['extraction_status']}")
        print(f"Confidence: {data['extraction']['confidence_score']}")
        print(f"Metadata: {data['extraction']['metadata']}")
    else:
        error = response.json()
        print(f"Error: {error['error']['message']}")

upload_pdf('certificate.pdf')
```

### TypeScript/Fetch Example

```typescript
interface UploadResponse {
  document: Document;
  extraction: ExtractionResult;
}

interface Document {
  id: number;
  filename: string;
  processing_status: string;
  uploaded_at: string;
}

interface ExtractionResult {
  id: number;
  document_id: number;
  extracted_text: string;
  metadata: Metadata;
  confidence_score: number;
  extraction_status: string;
}

interface Metadata {
  certificate_number?: string;
  issuing_organization?: string;
  issue_date?: string;
  expiry_date?: string;
  certified_company?: string;
  certification_scope?: string;
}

async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:3000/api/documents', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }

  return response.json();
}

// Usage
const fileInput = document.querySelector<HTMLInputElement>('#file-input');
fileInput?.addEventListener('change', async (event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  try {
    const result = await uploadDocument(file);
    console.log('Extraction results:', result.extraction.metadata);
  } catch (error) {
    console.error('Upload failed:', error);
  }
});
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing:

- Per-IP rate limits (e.g., 100 requests/hour)
- Upload size limits (configured via `MAX_FILE_SIZE`)
- Concurrent processing limits

## CORS

CORS is configured via the `CORS_ORIGIN` environment variable. Default is `http://localhost:3000`.

For multiple origins in production:

```javascript
// In src/index.ts or middleware
const allowedOrigins = process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'];
```

## Pagination

For large datasets, use pagination:

```bash
# Page 1 (documents 0-49)
curl "http://localhost:3000/api/documents?limit=50&offset=0"

# Page 2 (documents 50-99)
curl "http://localhost:3000/api/documents?limit=50&offset=50"

# Page 3 (documents 100-149)
curl "http://localhost:3000/api/documents?limit=50&offset=100"
```

## Filtering

Filter documents by processing status:

```bash
# Only completed documents
curl "http://localhost:3000/api/documents?status=completed"

# Only failed documents
curl "http://localhost:3000/api/documents?status=failed"

# Combine with pagination
curl "http://localhost:3000/api/documents?status=completed&limit=20&offset=0"
```

## Webhooks

Not currently implemented. Future enhancement could include webhook notifications when processing completes:

```json
{
  "event": "document.processed",
  "document_id": 1,
  "status": "completed",
  "extraction_status": "success",
  "timestamp": "2026-04-11T10:30:01.500Z"
}
```

## Performance

**Typical Response Times**:
- Upload + Process: 600-1000ms for 10-page PDF
- List Documents: 10-50ms
- Get Document by ID: 5-20ms

**Optimization Tips**:
- Use pagination for large document lists
- Cache frequently accessed documents
- Use database indexes (already configured)
- Consider CDN for serving processed results

## Support

For API issues:
- Check response status codes and error messages
- Enable debug logging: `LOG_LEVEL=debug`
- Review application logs
- Test with sample PDFs in `tests/fixtures/`
