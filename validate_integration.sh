#!/bin/bash

# Validation script for Username Enumeration API integration
# This script checks that all required components are in place

echo "=========================================="
echo "Username Enumeration API Validation"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((pass_count++))
    else
        echo -e "${RED}✗${NC} $1"
        ((fail_count++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((pass_count++))
    else
        echo -e "${RED}✗${NC} $1"
        ((fail_count++))
    fi
}

echo "Checking core files..."
check_file "backend/main.py"
check_file "backend/routes/username_enum.py"
check_file "backend/services/username_enum_service.py"
check_file "backend/models/schemas.py"
echo ""

echo "Checking utility modules..."
check_file "backend/utils/cache.py"
check_file "backend/utils/rate_limiter.py"
check_file "backend/utils/database.py"
check_file "backend/utils/neo4j_manager.py"
check_file "backend/utils/confidence_scorer.py"
check_file "backend/utils/pattern_detector.py"
check_file "backend/utils/platform_registry.py"
check_file "backend/utils/export.py"
check_file "backend/utils/websocket.py"
echo ""

echo "Checking test files..."
check_file "backend/tests/__init__.py"
check_file "backend/tests/test_username_enum_api.py"
check_file "backend/tests/test_database.py"
check_file "backend/tests/test_rate_limiting.py"
check_file "backend/tests/test_caching.py"
check_file "backend/tests/test_integration.py"
echo ""

echo "Checking documentation..."
check_file "backend/docs/USERNAME_ENUM_API.md"
check_file "backend/docs/INTEGRATION_GUIDE.md"
check_file "backend/docs/TESTING.md"
check_file "backend/docs/INTEGRATION_SUMMARY.md"
echo ""

echo "Checking configuration..."
check_file ".env.example"
check_file "pytest.ini"
check_file "requirements.txt"
echo ""

echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}${pass_count}${NC}"
echo -e "Failed: ${RED}${fail_count}${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed.${NC}"
    exit 1
fi
