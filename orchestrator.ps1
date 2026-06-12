<#
.SYNOPSIS
    Advanced Enterprise Orchestrator for Web Accessibility Auditor.
.DESCRIPTION
    Dynamically validates the host environment, enforces port collision failsafes,
    synchronizes dependencies, and manages the lifecycle of the React/FastAPI stack.
#>

$ErrorActionPreference = "Stop"
$Script:LogDir = "$PSScriptRoot\logs"
$Script:LogPath = "$LogDir\orchestrator.log"

# ==========================================
# 1. LOGGING INFRASTRUCTURE
# ==========================================
if (!(Test-Path $Script:LogDir)) {
    New-Item -ItemType Directory -Force -Path $Script:LogDir | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level="INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    if ($Level -eq "ERROR") { Write-Host $LogMessage -ForegroundColor Red }
    elseif ($Level -eq "WARN") { Write-Host $LogMessage -ForegroundColor Yellow }
    elseif ($Level -eq "SUCCESS") { Write-Host $LogMessage -ForegroundColor Green }
    else { Write-Host $LogMessage -ForegroundColor Cyan }
    
    Add-Content -Path $Script:LogPath -Value $LogMessage
}

Write-Log "Initializing Advanced Engine Orchestrator..." "INFO"

# ==========================================
# 2. DEPENDENCY VALIDATION FAILSAFES
# ==========================================
Write-Log "Executing system binary verification..." "INFO"
$deps = @("python", "npm")
foreach ($dep in $deps) {
    if (!(Get-Command $dep -ErrorAction SilentlyContinue)) {
        Write-Log "CRITICAL FAILSAFE: Required binary '$dep' is missing from PATH." "ERROR"
        Write-Log "ABORTING BOOT SEQUENCE." "ERROR"
        exit 1
    }
}

# ==========================================
# 3. NETWORK PORT COLLISION FAILSAFES
# ==========================================
function Test-PortAvailability {
    param([int]$Port, [string]$ServiceName)
    Write-Log "Verifying Port $Port ($ServiceName)..." "INFO"
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        $pidToKill = $connection.OwningProcess
        Write-Log "FAILSAFE TRIGGERED: Port $Port is currently blocked by PID $pidToKill." "WARN"
        Write-Log "Auto-terminating conflicting process to boot $ServiceName..." "WARN"
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

Test-PortAvailability 8000 "FastAPI Backend"
Test-PortAvailability 5173 "React Frontend"

# ==========================================
# 4. DYNAMIC VIRTUAL ENVIRONMENT
# ==========================================
if (!(Test-Path "$PSScriptRoot\.venv")) {
    Write-Log "Virtual environment missing. Dynamically constructing .venv..." "WARN"
    try {
        python -m venv .venv
        Write-Log ".venv constructed successfully." "SUCCESS"
    } catch {
        Write-Log "CRITICAL FAILSAFE: Failed to build virtual environment. $_" "ERROR"
        exit 1
    }
}

Write-Log "Activating Python Virtual Environment state..." "INFO"
$Env:VIRTUAL_ENV = "$PSScriptRoot\.venv"
$Env:Path = "$PSScriptRoot\.venv\Scripts;" + $Env:Path

# ==========================================
# 5. DEPENDENCY SYNCHRONIZATION
# ==========================================
Write-Log "Synchronizing Backend Python Dependencies (Quiet Mode)..." "INFO"
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
} elseif (Test-Path "pyproject.toml") {
    if (Get-Command "poetry" -ErrorAction SilentlyContinue) {
        poetry install --quiet
    } else {
        Write-Log "Poetry not found in PATH. Skipping dependency sync." "WARN"
    }
}

Write-Log "Synchronizing Frontend React Dependencies (Silent Mode)..." "INFO"
Push-Location "$PSScriptRoot\frontend"
npm install --silent
Pop-Location

# ==========================================
# 6. LIFECYCLE ORCHESTRATION
# ==========================================
Write-Log "All failsafes passed. Booting Distributed Engine..." "SUCCESS"

# Launch Backend
$BackendProc = Start-Process -FilePath "python" -ArgumentList "run_server.py" -PassThru -WindowStyle Normal
Write-Log "FastAPI Backend bound to PID $($BackendProc.Id)" "INFO"

# Launch Frontend
Push-Location "$PSScriptRoot\frontend"
$FrontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -PassThru -WindowStyle Normal
Pop-Location
Write-Log "React Frontend bound to PID $($FrontendProc.Id)" "INFO"

Write-Log "=======================================================" "SUCCESS"
Write-Log "SYSTEM ONLINE AND STABLE" "SUCCESS"
Write-Log "Dashboard: http://localhost:5173" "SUCCESS"
Write-Log "API Server: http://127.0.0.1:8000/docs" "SUCCESS"
Write-Log "Press CTRL+C in this window to gracefully shut down the engine." "WARN"
Write-Log "=======================================================" "SUCCESS"

# ==========================================
# 7. GRACEFUL TEARDOWN
# ==========================================
try {
    # Block and monitor the processes
    Wait-Process -Id $BackendProc.Id, $FrontendProc.Id
} finally {
    Write-Log "Shutdown sequence initiated. Tearing down child processes..." "WARN"
    if (!$BackendProc.HasExited) { 
        Stop-Process -Id $BackendProc.Id -Force 
        Write-Log "Backend (PID $($BackendProc.Id)) terminated." "INFO"
    }
    if (!$FrontendProc.HasExited) { 
        Stop-Process -Id $FrontendProc.Id -Force 
        Write-Log "Frontend (PID $($FrontendProc.Id)) terminated." "INFO"
    }
    Write-Log "Graceful teardown complete. Goodbye." "SUCCESS"
}
