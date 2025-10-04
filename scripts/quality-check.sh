#!/bin/bash
# Code quality check script
# Runs Black, Ruff, and Mypy on the codebase

set -e

echo "🔍 Running code quality checks..."
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

# 1. Black formatting check
echo -e "${BLUE}1. Checking code formatting with Black...${NC}"
uv run black --check backend/ || {
    echo "❌ Code formatting issues found. Run 'black backend/' to fix."
    exit 1
}
echo -e "${GREEN}✓ Code formatting passed${NC}"
echo ""

# 2. Ruff linting
echo -e "${BLUE}2. Running Ruff linter...${NC}"
uv run ruff check backend/ || {
    echo "❌ Linting issues found. Run 'ruff check backend/ --fix' to auto-fix."
    exit 1
}
echo -e "${GREEN}✓ Linting passed${NC}"
echo ""

# 3. Mypy type checking
echo -e "${BLUE}3. Running Mypy type checker...${NC}"
uv run mypy backend/ || {
    echo "❌ Type checking issues found."
    exit 1
}
echo -e "${GREEN}✓ Type checking passed${NC}"
echo ""

echo -e "${GREEN}🎉 All quality checks passed!${NC}"
