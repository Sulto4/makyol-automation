# Makyol Compliance API

REST API for querying supplier compliance data and integrating with external systems (ERP, procurement platforms, project management tools).

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Development](#development)
- [Testing](#testing)
- [API Documentation](#api-documentation)

## Features

- 🔐 **Secure Access**: API key authentication on all endpoints
- ⚡ **Rate Limited**: 100 requests/minute to prevent abuse
- 📊 **Rich Data**: Comprehensive compliance, supplier, and document information
- 🔍 **Flexible Querying**: Filtering, pagination, and search capabilities
- 📝 **Well Documented**: OpenAPI/Swagger specification with examples
- ✅ **Fully Tested**: Comprehensive test suite with 158+ tests

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd makyol-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set your API keys

# 4. Start the server
uvicorn app.main:app --reload

# 5. Access the API
# API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependencies Include

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation using Python type hints
- **SlowAPI**: Rate limiting middleware
- **pytest**: Testing framework
- **httpx**: HTTP client for testing

## Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Application Configuration
APP_NAME="Makyol Compliance API"
APP_VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=true

# Server Configuration
HOST="0.0.0.0"
PORT=8000

# API Security
# Generate secure API keys: openssl rand -hex 32
API_KEYS="your-secure-api-key-here,another-api-key-here"

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL="INFO"
```

### Generate API Keys

```bash
# Generate a secure API key
openssl rand -hex 32

# Example output: 5f9c7b2a8d4e6f1a3c5b7d9e2f4a6c8b1d3e5f7a9b2c4d6e8f1a3b5c7d9e2f4a
```

Add the generated key to the `API_KEYS` variable in your `.env` file.

## Authentication

All API endpoints (except `/health` and `/`) require authentication using an API key.

### Include API Key in Request Headers

```bash
X-API-Key: your-api-key-here
```

### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/suppliers" \
  -H "X-API-Key: your-api-key-here"
```

### Authentication Errors

- **401 Unauthorized**: Missing or invalid API key
- **429 Too Many Requests**: Rate limit exceeded

## API Endpoints

### System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check endpoint | No |
| GET | `/` | API root with basic info | No |

### Suppliers

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/suppliers` | List all suppliers with filtering and pagination | Yes |
| GET | `/api/v1/suppliers/{id}` | Get supplier details by ID | Yes |

**Query Parameters for List:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (1-100, default: 10)
- `category` (string): Filter by category (construction, equipment, consulting, labor, other)
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name, registration number, or contact person

### Compliance

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/compliance/suppliers/{id}` | Get compliance status for a supplier | Yes |

### Documents

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/documents` | List all documents with filtering and pagination | Yes |
| GET | `/api/v1/documents/{id}` | Get document details by ID | Yes |

**Query Parameters for List:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (1-100, default: 10)
- `supplier_id` (int): Filter by supplier ID
- `document_type` (string): Filter by type (registration, tax, insurance, license, financial, quality, safety, contract, other)
- `status` (string): Filter by status (valid, expired, expiring_soon, pending_review, rejected, archived)
- `is_required` (boolean): Filter by required status
- `search` (string): Search in document name, supplier name, or validation notes

### Alerts

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/alerts/expiry` | Get document expiry alerts | Yes |

**Query Parameters:**
- `days` (int): Number of days to check for expiry (1-365, default: 30)
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (1-100, default: 10)
- `document_type` (string): Filter by document type
- `supplier_id` (int): Filter by supplier ID

### Reports

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/reports/compliance` | Generate compliance reports | Yes |

**Query Parameters:**
- `period` (string): Reporting period (current_month, last_month, current_quarter, last_quarter, current_year, last_year, all_time; default: current_month)
- `format` (string): Output format (json, summary; default: json)
- `include_details` (boolean): Include detailed statistics (default: true)

## Usage Examples

### 1. List Active Suppliers

```bash
curl -X GET "http://localhost:8000/api/v1/suppliers?is_active=true&page=1&limit=10" \
  -H "X-API-Key: your-api-key-here"
```

### 2. Get Supplier by ID

```bash
curl -X GET "http://localhost:8000/api/v1/suppliers/1" \
  -H "X-API-Key: your-api-key-here"
```

### 3. Check Supplier Compliance Status

```bash
curl -X GET "http://localhost:8000/api/v1/compliance/suppliers/1" \
  -H "X-API-Key: your-api-key-here"
```

### 4. List Documents for a Supplier

```bash
curl -X GET "http://localhost:8000/api/v1/documents?supplier_id=1&status=valid" \
  -H "X-API-Key: your-api-key-here"
```

### 5. Get Expiring Documents (Next 30 Days)

```bash
curl -X GET "http://localhost:8000/api/v1/alerts/expiry?days=30" \
  -H "X-API-Key: your-api-key-here"
```

### 6. Generate Compliance Report

```bash
curl -X GET "http://localhost:8000/api/v1/reports/compliance?period=current_month&format=json" \
  -H "X-API-Key: your-api-key-here"
```

### Python Example

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY
}

# Get all active suppliers
response = requests.get(
    f"{API_URL}/api/v1/suppliers",
    headers=headers,
    params={"is_active": True, "page": 1, "limit": 10}
)

if response.status_code == 200:
    data = response.json()
    print(f"Total suppliers: {data['total']}")
    for supplier in data['data']:
        print(f"- {supplier['name']} ({supplier['category']})")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

### JavaScript/TypeScript Example

```javascript
const API_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key-here';

// Get expiring documents
async function getExpiringDocuments(days = 30) {
  const response = await fetch(
    `${API_URL}/api/v1/alerts/expiry?days=${days}`,
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );

  if (response.ok) {
    const data = await response.json();
    console.log(`Documents expiring in ${days} days:`, data.total);
    return data.data;
  } else {
    const error = await response.json();
    throw new Error(`API Error: ${error.detail}`);
  }
}

getExpiringDocuments(30)
  .then(documents => console.log(documents))
  .catch(error => console.error(error));
```

## Rate Limiting

The API enforces rate limiting to prevent abuse:

- **Default Limit**: 100 requests per minute per API key
- **Response Status**: `429 Too Many Requests` when limit exceeded
- **Headers**: Rate limit information included in response headers

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617123456
```

### Handling Rate Limits

```python
import time
import requests

def make_api_request(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limited - wait and retry
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

## Error Handling

The API returns consistent JSON error responses:

### Error Response Format

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

### Common Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Handling Example

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/suppliers/999",
    headers={"X-API-Key": "your-api-key-here"}
)

if response.status_code == 200:
    supplier = response.json()
    print(supplier)
elif response.status_code == 404:
    print("Supplier not found")
elif response.status_code == 401:
    print("Invalid API key")
else:
    error = response.json()
    print(f"Error {response.status_code}: {error.get('detail')}")
```

## Development

### Run Development Server

```bash
# Standard mode
uvicorn app.main:app --reload

# Custom host and port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
uvicorn app.main:app --reload --log-level debug
```

### Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application and configuration
├── config.py            # Settings and environment configuration
├── models/              # Pydantic models
│   ├── __init__.py
│   ├── supplier.py      # Supplier models
│   ├── document.py      # Document models
│   ├── alert.py         # Alert models
│   ├── report.py        # Report models
│   └── common.py        # Common response models
├── routers/             # API route handlers
│   ├── __init__.py
│   ├── test.py          # Test endpoints
│   ├── suppliers.py     # Supplier endpoints
│   ├── compliance.py    # Compliance endpoints
│   ├── documents.py     # Document endpoints
│   ├── alerts.py        # Alert endpoints
│   └── reports.py       # Report endpoints
├── middleware/          # Custom middleware
│   ├── __init__.py
│   ├── auth.py          # API key authentication
│   ├── rate_limit.py    # Rate limiting
│   └── error_handler.py # Error handling
└── utils/               # Utility functions
    ├── __init__.py
    └── api_keys.py      # API key validation
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_suppliers.py -v

# Run specific test
pytest tests/test_auth.py::test_valid_api_key -v
```

### Test Coverage

The project includes comprehensive tests:

- **Authentication Tests**: 23 tests covering API key validation, CORS, and error handling
- **Rate Limiting Tests**: 7 tests for rate limit enforcement
- **Supplier Tests**: 30 tests for supplier endpoints
- **Document Tests**: 30 tests for document endpoints
- **Compliance Tests**: 22 tests for compliance status
- **Alert Tests**: 27 tests for expiry alerts
- **Report Tests**: 29 tests for compliance reports

**Total: 158+ tests**

### Test Examples

```bash
# Test authentication
pytest tests/test_auth.py -v

# Test rate limiting
pytest tests/test_rate_limit.py -v

# Test all endpoints
pytest tests/test_suppliers.py tests/test_documents.py tests/test_compliance.py -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## API Documentation

### Interactive Documentation

The API provides auto-generated interactive documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Interactive API explorer
  - Try out endpoints directly in the browser
  - See request/response examples

- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - Clean, readable API documentation
  - Searchable endpoint reference
  - Detailed schema documentation

### OpenAPI Specification

- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
  - Machine-readable API specification
  - Can be imported into tools like Postman, Insomnia, or API testing frameworks

## Use Cases

### 1. ERP Integration

Check supplier compliance before generating purchase orders:

```python
def can_create_purchase_order(supplier_id: int) -> bool:
    """Check if a supplier is compliant before creating a PO."""
    response = requests.get(
        f"{API_URL}/api/v1/compliance/suppliers/{supplier_id}",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        compliance = response.json()
        return compliance['compliance_status'] == 'compliant'
    
    return False
```

### 2. Procurement Automation

Automate supplier verification workflows:

```python
def verify_all_suppliers():
    """Check compliance status for all active suppliers."""
    suppliers_response = requests.get(
        f"{API_URL}/api/v1/suppliers",
        headers={"X-API-Key": API_KEY},
        params={"is_active": True, "limit": 100}
    )
    
    results = []
    for supplier in suppliers_response.json()['data']:
        compliance_response = requests.get(
            f"{API_URL}/api/v1/compliance/suppliers/{supplier['id']}",
            headers={"X-API-Key": API_KEY}
        )
        results.append({
            "supplier": supplier['name'],
            "status": compliance_response.json()['compliance_status']
        })
    
    return results
```

### 3. Project Management Dashboard

Display compliance status in project dashboards:

```javascript
async function getProjectSupplierStatus(projectId) {
  // Get suppliers for project (assumes you have project-supplier mapping)
  const suppliers = await getProjectSuppliers(projectId);
  
  const complianceData = await Promise.all(
    suppliers.map(async (supplier) => {
      const response = await fetch(
        `${API_URL}/api/v1/compliance/suppliers/${supplier.id}`,
        { headers: { 'X-API-Key': API_KEY } }
      );
      const compliance = await response.json();
      
      return {
        supplierId: supplier.id,
        supplierName: supplier.name,
        status: compliance.compliance_status,
        score: compliance.compliance_score
      };
    })
  );
  
  return complianceData;
}
```

### 4. Automated Alerts

Monitor and alert on expiring documents:

```python
def send_expiry_alerts(days=30):
    """Send alerts for documents expiring within specified days."""
    response = requests.get(
        f"{API_URL}/api/v1/alerts/expiry",
        headers={"X-API-Key": API_KEY},
        params={"days": days, "limit": 100}
    )
    
    if response.status_code == 200:
        expiring_docs = response.json()['data']
        
        for doc in expiring_docs:
            send_notification(
                to=doc['supplier_name'],
                subject=f"Document Expiring Soon: {doc['document_name']}",
                body=f"Your {doc['document_type']} document expires on {doc['expiry_date']}"
            )
```

## License

Proprietary - Makyol

## Support

For API support and questions:
- **Email**: it@makyol.com
- **Website**: https://makyol.com

---

**Version**: 1.0.0  
**Last Updated**: April 2026
