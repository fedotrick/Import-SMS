#!/bin/bash
# Master test runner script

set -e

echo "======================================"
echo "RUNNING ALL TESTS"
echo "======================================"

cd "$(dirname "$0")"

# Count tests
TOTAL_TESTS=0
PASSED_TESTS=0

echo -e "\n======================================"
echo "1. Parser Tests"
echo "======================================"
if python tests/test_parser.py; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -e "\n======================================"
echo "2. Concurrent Excel Write Tests"
echo "======================================"
if python tests/test_excel_concurrent_simple.py; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -e "\n======================================"
echo "3. Docker Configuration Tests"
echo "======================================"
if bash tests/test_docker.sh; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -e "\n======================================"
echo "TEST SUMMARY"
echo "======================================"
echo "Passed: $PASSED_TESTS/$TOTAL_TESTS test suites"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
