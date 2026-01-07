#!/bin/bash

# Study Assistant MCP - Quick Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "======================================"
echo "Study Assistant MCP - Quick Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.11+ is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Edit .env file with your API keys before proceeding${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/cache data/uploads data/processed
echo -e "${GREEN}✓ Data directories created${NC}"

# Run tests
echo ""
echo "Would you like to run tests? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Running tests..."
    pytest tests/ -v
    echo -e "${GREEN}✓ Tests completed${NC}"
fi

# Summary
echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   - GOOGLE_API_KEY (from ai.google.dev)"
echo "   - GROQ_API_KEY (from console.groq.com)"
echo "   - NOTION_API_KEY (from notion.so/my-integrations)"
echo ""
echo "2. Test API connections:"
echo "   python scripts/test_apis.py"
echo ""
echo "3. Set up Notion workspace:"
echo "   python scripts/setup_notion.py"
echo ""
echo "4. Start processing notes!"
echo ""
echo -e "${GREEN}Happy studying! 📚${NC}"