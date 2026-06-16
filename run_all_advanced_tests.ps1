# Run All Advanced Tests - PowerShell

Write-Host "========================================"
Write-Host "Starting Advanced Backend Pytest Suite"
Write-Host "========================================"

# Run backend tests with coverage
poetry run pytest --cov=src --cov-report=term-missing -v

if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend tests failed!" -ForegroundColor Red
} else {
    Write-Host "Backend tests passed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================"
Write-Host "Starting Advanced Frontend Vitest Suite"
Write-Host "========================================"

# Navigate to frontend and run vitest
Push-Location frontend
npm run test
$frontend_exit = $LASTEXITCODE
Pop-Location

if ($frontend_exit -ne 0) {
    Write-Host "Frontend tests failed!" -ForegroundColor Red
} else {
    Write-Host "Frontend tests passed!" -ForegroundColor Green
}
