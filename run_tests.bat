@echo off
SETLOCAL EnableDelayedExpansion

echo ======================================================
echo   ACCESSIBILITY AUDITOR: AUTOMATED TESTING GATEWAY   
echo ======================================================
echo.

:: Step 1: Ensure Reports Log Directory is Present
if not exist "reports\logs" mkdir reports\logs

:: Step 2: Detect Environment and Run Pytest
where poetry >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Poetry detected. Initializing dependencies...
    call poetry install --only main,dev
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Poetry dependency synchronization failed. Attempting execution anyway...
    )
    echo [INFO] Running test suite via Poetry...
    call poetry run pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    set TEST_RESULT=%ERRORLEVEL%
    goto END
)

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Local virtual environment (.venv) detected. Activating...
    call .venv\Scripts\activate.bat
    echo [INFO] Running test suite via local virtual environment...
    call pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    set TEST_RESULT=%ERRORLEVEL%
    goto END
)

:: Fallback to system python/pytest
echo [WARNING] Poetry and local .venv not found. Falling back to system pytest...
where pytest >nul 2>nul
if %ERRORLEVEL% equ 0 (
    call pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    set TEST_RESULT=%ERRORLEVEL%
) else (
    echo [INFO] Trying python -m pytest...
    python -m pytest --cov=src/auditor --cov-report=term-missing --cov-report=html tests/
    set TEST_RESULT=%ERRORLEVEL%
)

:END
if %TEST_RESULT% equ 0 (
    echo.
    echo ======================================================
    echo   [SUCCESS] All tests passed successfully.
    echo   Coverage report saved to: htmlcov/index.html
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo   [FAILURE] Test execution failed with code %TEST_RESULT%
    echo ======================================================
)

exit /b %TEST_RESULT%

