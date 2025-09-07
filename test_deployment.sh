#!/bin/bash

echo "🧪 Testing Flight Scraper Deployment"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    echo -n "Testing $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local description=$2
    
    echo -n "Testing $description... "
    
    response=$(curl -s "$url")
    
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC} (Valid JSON)"
    else
        echo -e "${RED}✗ FAIL${NC} (Invalid JSON)"
    fi
}

echo ""
echo "1. Testing Container Status"
echo "---------------------------"
docker-compose ps

echo ""
echo "2. Testing Backend API"
echo "----------------------"
test_endpoint "http://localhost:8000/health" "200" "Health Check"
test_endpoint "http://localhost:8000/" "200" "Root Endpoint"
test_endpoint "http://localhost:8000/docs" "200" "API Documentation"
test_json_endpoint "http://localhost:8000/api/v1/dashboard/stats" "Dashboard Stats"

echo ""
echo "3. Testing Frontend"
echo "-------------------"
test_endpoint "http://localhost:3000" "200" "Frontend Application"

echo ""
echo "4. Testing Database Connection"
echo "------------------------------"
echo -n "Testing PostgreSQL connection... "
if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""
echo "5. Testing Redis Connection"
echo "---------------------------"
echo -n "Testing Redis connection... "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""
echo "6. Testing Celery Worker"
echo "------------------------"
echo -n "Testing Celery worker... "
if docker-compose exec -T celery celery -A app.core.celery inspect ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""
echo "🎉 Deployment Test Complete!"
echo "============================"
echo ""
echo "Access URLs:"
echo "• Frontend: http://localhost:3000"
echo "• Backend API: http://localhost:8000"
echo "• API Docs: http://localhost:8000/docs"
echo ""
echo "Demo Credentials:"
echo "• Username: admin"
echo "• Password: admin123"
echo ""
echo "Note: You may need to create the demo user first using the setup instructions."
