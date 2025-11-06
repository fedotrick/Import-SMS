#!/bin/bash
# Project validation script - checks that all components are in place

set -e

echo "======================================"
echo "PROJECT VALIDATION"
echo "======================================"

cd "$(dirname "$0")"

ERRORS=0

# Check source files
echo -e "\n1. Checking source files..."
files=(
    "src/bot/services/parser.py"
    "src/bot/services/excel.py"
    "src/bot/handlers/add_record.py"
    "src/bot/handlers/menu.py"
    "src/bot/handlers/start.py"
    "src/bot/keyboards/main_menu.py"
    "src/core/config.py"
    "main.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check test files
echo -e "\n2. Checking test files..."
test_files=(
    "tests/test_parser.py"
    "tests/test_excel_concurrent_simple.py"
    "tests/test_docker.sh"
    "tests/example_shift_report.txt"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check documentation
echo -e "\n3. Checking documentation..."
docs=(
    "README.md"
    "TEST_REPORT.md"
    "SHIFT_REPORT_FORMAT.md"
    "TESTING_SUMMARY.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✓ $doc"
    else
        echo "  ✗ $doc (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check configuration
echo -e "\n4. Checking configuration..."
config_files=(
    ".env"
    ".env.example"
    ".gitignore"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check directories
echo -e "\n5. Checking directories..."
if [ -d "Контроль" ]; then
    echo "  ✓ Контроль/ directory exists"
else
    echo "  ⚠️  Контроль/ directory missing (will be created on first run)"
fi

if [ -d "src" ]; then
    echo "  ✓ src/ directory exists"
else
    echo "  ✗ src/ directory missing"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "tests" ]; then
    echo "  ✓ tests/ directory exists"
else
    echo "  ✗ tests/ directory missing"
    ERRORS=$((ERRORS + 1))
fi

# Check Python syntax
echo -e "\n6. Checking Python syntax..."
if python -m py_compile src/bot/services/parser.py 2>/dev/null; then
    echo "  ✓ parser.py syntax OK"
else
    echo "  ✗ parser.py has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

if python -m py_compile src/bot/services/excel.py 2>/dev/null; then
    echo "  ✓ excel.py syntax OK"
else
    echo "  ✗ excel.py has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

if python -m py_compile src/bot/handlers/add_record.py 2>/dev/null; then
    echo "  ✓ add_record.py syntax OK"
else
    echo "  ✗ add_record.py has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

# Check key implementations
echo -e "\n7. Checking key implementations..."

if grep -q "class PlavkaRecord" src/bot/services/parser.py; then
    echo "  ✓ PlavkaRecord class found in parser.py"
else
    echo "  ✗ PlavkaRecord class missing in parser.py"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "def parse_shift_report" src/bot/services/parser.py; then
    echo "  ✓ parse_shift_report function found"
else
    echo "  ✗ parse_shift_report function missing"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "PLAVKA_HEADERS" src/bot/services/excel.py; then
    echo "  ✓ PLAVKA_HEADERS defined in excel.py"
else
    echo "  ✗ PLAVKA_HEADERS missing in excel.py"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "def append_plavka_rows" src/bot/services/excel.py; then
    echo "  ✓ append_plavka_rows function found"
else
    echo "  ✗ append_plavka_rows function missing"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo -e "\n======================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ VALIDATION PASSED"
    echo "All components are in place!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: ./run_all_tests.sh"
    echo "  2. Set BOT_TOKEN in .env"
    echo "  3. Start bot: python main.py"
    echo "     or with Docker: docker compose up -d"
    exit 0
else
    echo "❌ VALIDATION FAILED"
    echo "Found $ERRORS error(s)"
    echo "======================================"
    exit 1
fi
