@echo off
echo ========================================
echo Starting Advanced Backend Pytest Suite
echo ========================================

REM Run backend tests with coverage
call poetry run pytest --cov=src --cov-report=term-missing -v

if %ERRORLEVEL% neq 0 (
    echo Backend tests failed!
) else (
    echo Backend tests passed!
)

echo.
echo ========================================
echo Starting Advanced Frontend Vitest Suite
echo ========================================

REM Navigate to frontend and run vitest
cd frontend
call npm run test
set FRONTEND_EXIT=%ERRORLEVEL%
cd ..

if %FRONTEND_EXIT% neq 0 (
    echo Frontend tests failed!
) else (
    echo Frontend tests passed!
)
