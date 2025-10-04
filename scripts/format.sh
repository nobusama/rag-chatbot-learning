#!/bin/bash
# Auto-format code with Black and Ruff

set -e

echo "🔧 Formatting code..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must be run from project root directory"
    exit 1
fi

# 1. Black formatting
echo -e "${BLUE}1. Formatting with Black...${NC}"
uv run black backend/
echo -e "${GREEN}✓ Black formatting complete${NC}"
echo ""

# 2. Ruff auto-fix
echo -e "${BLUE}2. Auto-fixing with Ruff...${NC}"
uv run ruff check backend/ --fix
echo -e "${GREEN}✓ Ruff auto-fix complete${NC}"
echo ""

# 3. Import sorting
echo -e "${BLUE}3. Sorting imports with Ruff...${NC}"
uv run ruff check backend/ --select I --fix
echo -e "${GREEN}✓ Import sorting complete${NC}"
echo ""

echo -e "${GREEN}🎉 Code formatting complete!${NC}"
echo "Run './scripts/quality-check.sh' to verify all checks pass."
