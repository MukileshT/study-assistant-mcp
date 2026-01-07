#!/bin/bash

# Test runner script with multiple options

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "Study Assistant MCP - Test Runner"
echo -e "======================================${NC}\n"

# Parse arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}\n"
        pytest tests/ -m "unit" -v
        ;;
    
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}\n"
        pytest tests/test_integration.py -v
        ;;
    
    e2e)
        echo -e "${YELLOW}Running end-to-end tests...${NC}\n"
        echo -e "${RED}WARNING: E2E tests require valid API keys${NC}"
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pytest tests/test_e2e.py -v -m "e2e"
        fi
        ;;
    
    fast)
        echo -e "${YELLOW}Running fast tests only...${NC}\n"
        pytest tests/ -m "not slow and not e2e" -v
        ;;
    
    coverage)
        echo -e "${YELLOW}Running tests with coverage report...${NC}\n"
        pytest tests/ --cov=src --cov-report=html --cov-report=term
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify test file or function${NC}"
            echo "Usage: ./scripts/run_tests.sh specific tests/test_file.py::test_function"
            exit 1
        fi
        echo -e "${YELLOW}Running specific test: $2${NC}\n"
        pytest "$2" -v
        ;;
    
    all)
        echo -e "${YELLOW}Running all tests (excluding e2e)...${NC}\n"
        pytest tests/ -m "not e2e" -v
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: ./scripts/run_tests.sh [TEST_TYPE]"
        echo ""
        echo "Test types:"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests"
        echo "  e2e          - Run end-to-end tests (requires API keys)"
        echo "  fast         - Run fast tests only (no slow or e2e)"
        echo "  coverage     - Run with coverage report"
        echo "  specific     - Run specific test file/function"
        echo "  all          - Run all tests except e2e (default)"
        echo ""
        exit 1
        ;;
esac

# Exit status
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi