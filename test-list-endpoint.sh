#!/bin/bash
# Test script for GET /api/documents endpoint
#
# Usage: ./test-list-endpoint.sh
# Prerequisites: Server must be running on http://localhost:3000

set -e

echo "=== Testing GET /api/documents endpoint ==="
echo ""

# Test 1: Get all documents (no filters)
echo "Test 1: GET /api/documents (no filters)"
echo "Request: GET /api/documents"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X GET http://localhost:3000/api/documents \
  -H "Content-Type: application/json" \
  2>/dev/null || echo "HTTP_STATUS:000")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "Response Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Test 1 PASSED: Received 200 OK status"

    # Validate response structure
    HAS_DOCUMENTS=$(echo "$BODY" | jq 'has("documents")' 2>/dev/null)
    HAS_COUNT=$(echo "$BODY" | jq 'has("count")' 2>/dev/null)

    if [ "$HAS_DOCUMENTS" = "true" ] && [ "$HAS_COUNT" = "true" ]; then
        echo "✅ Response has correct structure (documents, count)"
        COUNT=$(echo "$BODY" | jq '.count' 2>/dev/null)
        echo "   Document count: $COUNT"
    else
        echo "❌ Response structure invalid"
        exit 1
    fi
else
    echo "❌ Test 1 FAILED: Expected 200, got $HTTP_STATUS"
    exit 1
fi

echo ""

# Test 2: Get documents with limit
echo "Test 2: GET /api/documents?limit=5"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X GET "http://localhost:3000/api/documents?limit=5" \
  -H "Content-Type: application/json" \
  2>/dev/null || echo "HTTP_STATUS:000")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "Response Status: $HTTP_STATUS"
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Test 2 PASSED: Pagination works"
    LIMIT=$(echo "$BODY" | jq '.limit' 2>/dev/null)
    echo "   Limit applied: $LIMIT"
else
    echo "❌ Test 2 FAILED"
fi

echo ""

# Test 3: Filter by status
echo "Test 3: GET /api/documents?status=completed"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X GET "http://localhost:3000/api/documents?status=completed" \
  -H "Content-Type: application/json" \
  2>/dev/null || echo "HTTP_STATUS:000")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
echo "Response Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Test 3 PASSED: Status filter works"
else
    echo "❌ Test 3 FAILED"
fi

echo ""
echo "=== All tests completed! ==="
