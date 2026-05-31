#!/usr/bin/env bash

echo "======================================================"
echo "  ACCESSIBILITY AUDITOR: AUTOMATED TESTING GATEWAY   "
echo "======================================================"
echo

# Ensure logs directory exists
mkdir -p reports/logs

# Step 1: Detect Environment and Run Pytest
if command -v poetry &> /dev/null; then
    echo "[INFO] Poetry detected. Initializing dependencies..."
    poetry install --only main,dev || echo "[WARNING] Poetry install failed. Proceeding anyway..."
    echo "[INFO] Running test suite via Poetry..."
    poetry run pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    TEST_RESULT=$?
elif [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Local virtual environment (.venv) detected. Activating..."
    source .venv/bin/activate
    echo "[INFO] Running test suite via local virtual environment..."
    pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    TEST_RESULT=$?
else
    echo "[WARNING] Poetry and local .venv not found. Falling back to system python/pytest..."
    if command -v pytest &> /dev/null; then
        pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
        TEST_RESULT=$?
    else
        python3 -m pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
        TEST_RESULT=$?
    fi
fi

if [ $TEST_RESULT -eq 0 ]; then
    echo
    echo "======================================================"
    echo "  [SUCCESS] All tests passed successfully."
    echo "  Coverage report saved to: htmlcov/index.html"
    echo "======================================================"
else
    echo
    echo "======================================================"
    echo "  [FAILURE] Test execution failed with code $TEST_RESULT"
    echo "======================================================"
fi

exit $TEST_RESULT

