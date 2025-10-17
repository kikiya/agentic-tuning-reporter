#!/bin/bash

# Test the agent generate-report endpoint
# Make sure both services are running:
# - Main API Service on port 8001
# - Agent Service on port 8002

echo "Testing Agent Generate Report Endpoint..."
echo ""

# Test with default parameters
echo "1. Testing with default parameters (database=bookly, app=bookly):"
curl -X POST "http://localhost:8002/generate-report" \
  -H "Content-Type: application/json" \
  -d '{
    "database": "bookly",
    "app": "bookly"
  }' | jq '.'

echo ""
echo ""

# Test with custom prompt
echo "2. Testing with custom prompt:"
curl -X POST "http://localhost:8002/generate-report" \
  -H "Content-Type: application/json" \
  -d '{
    "database": "bookly",
    "app": "bookly",
    "prompt": "Give me a quick summary of the cluster topology and CPU usage."
  }' | jq '.'

echo ""
echo ""

# Test health endpoint
echo "3. Testing agent health endpoint:"
curl -X GET "http://localhost:8002/health" | jq '.'
