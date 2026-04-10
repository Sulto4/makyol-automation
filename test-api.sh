#!/bin/bash
# Test script for POST /api/documents endpoint
#
# Usage: ./test-api.sh
# Prerequisites: Server must be running on http://localhost:3000

set -e

echo "=== Testing POST /api/documents endpoint ==="
echo ""

# Get the absolute path to the test PDF
TEST_PDF="$(pwd)/tests/fixtures/sample.pdf"

if [ ! -f "$TEST_PDF" ]; then
    echo "❌ Error: Test PDF not found at $TEST_PDF"
    exit 1
fi

echo "✓ Test PDF found: $TEST_PDF"
echo ""

# Test 1: Upload with file_path
echo "Test 1: Upload PDF via file_path parameter"
echo "Request: POST /api/documents"
echo "Body: {\"file_path\": \"$TEST_PDF\"}"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST http://localhost:3000/api/documents \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$TEST_PDF\"}" \
  2>/dev/null || echo "HTTP_STATUS:000")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "Response Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_STATUS" = "201" ]; then
    echo "✅ Test PASSED: Received 201 Created status"

    # Parse and display key fields
    DOCUMENT_ID=$(echo "$BODY" | jq -r '.document.id' 2>/dev/null)
    PROCESSING_STATUS=$(echo "$BODY" | jq -r '.document.processing_status' 2>/dev/null)
    EXTRACTION_STATUS=$(echo "$BODY" | jq -r '.extraction.extraction_status' 2>/dev/null)
    CONFIDENCE=$(echo "$BODY" | jq -r '.extraction.confidence_score' 2>/dev/null)

    echo ""
    echo "Document ID: $DOCUMENT_ID"
    echo "Processing Status: $PROCESSING_STATUS"
    echo "Extraction Status: $EXTRACTION_STATUS"
    echo "Confidence Score: $CONFIDENCE"
else
    echo "❌ Test FAILED: Expected 201, got $HTTP_STATUS"
    exit 1
fi

echo ""
echo "=== All tests passed! ==="
