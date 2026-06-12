<#
.SYNOPSIS
    Advanced Enterprise System Purge Utility for Web Accessibility Auditor.
.DESCRIPTION
    Dynamically clears Python caches, React caches, and triggers the Python-level
    database and cache flush. Built with strict error handling, retries, and logging.
#>

$ErrorActionPreference = "Stop"
$Script:LogDir = "$PSScriptRoot\logs"
$Script:LogPath = "$LogDir\system_purge.log"

if (!(Test-Path $Script:LogDir)) {
    New-Item -ItemType Directory -Force -Path $Script:LogDir | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level="INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    if ($Level -eq "ERROR" -or $Level -eq "CRITICAL") { Write-Host $LogMessage -ForegroundColor Red }
    elseif ($Level -eq "WARN") { Write-Host $LogMessage -ForegroundColor Yellow }
    elseif ($Level -eq "SUCCESS") { Write-Host $LogMessage -ForegroundColor Green }
    else { Write-Host $LogMessage -ForegroundColor Cyan }
    
    Add-Content -Path $Script:LogPath -Value $LogMessage
}

function Remove-ItemWithRetry {
    param(
        [string]$Path,
        [int]$MaxRetries = 3
    )
    $attempt = 0
    while ($attempt -lt $MaxRetries) {
        try {
            if (Test-Path $Path) {
                Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            }
            return
        } catch {
            $attempt++
            if ($attempt -eq $MaxRetries) {
                Write-Log "Failed to remove '$Path' after $MaxRetries attempts. Locked by a zombie process?" "WARN"
            } else {
                Start-Sleep -Seconds 1
            }
        }
    }
}

Write-Log "=======================================================" "INFO"
Write-Log "  INITIALIZING TOTAL SYSTEM PURGE SEQUENCE" "INFO"
Write-Log "=======================================================" "INFO"

# 1. Validate dependencies
if (!(Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Log "CRITICAL FAILSAFE: Python binary not found. Cannot run database purge." "CRITICAL"
    exit 1
}

# 2. Execute Python Database Purge
Write-Log "[1/3] Executing Python Data Purge (SQLite, Neo4j, Redis, Files)..." "INFO"
try {
    # Dynamically utilize the Virtual Environment if it exists to ensure SQLModel dependencies are met
    if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
        Write-Log "Engine detected. Using strict Virtual Environment Python..." "INFO"
        $PythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
    } else {
        $PythonExe = "python"
    }

    $PurgeProcess = Start-Process -FilePath $PythonExe -ArgumentList "clear_data.py" -Wait -NoNewWindow -PassThru
    if ($PurgeProcess.ExitCode -ne 0) {
        Write-Log "Python purge utility returned non-zero exit code ($($PurgeProcess.ExitCode))." "WARN"
    } else {
        Write-Log "Python Data Purge completed successfully." "SUCCESS"
    }
} catch {
    Write-Log "Failed to execute Python clear_data.py script: $_" "CRITICAL"
    exit 1
}

# 3. Local Cache Annihilation
Write-Log "[2/3] Eradicating Local Cache Dependencies..." "INFO"

Write-Log "Scanning and destroying __pycache__ directories..." "INFO"
$PyCaches = Get-ChildItem -Path $PSScriptRoot -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue
foreach ($cache in $PyCaches) {
    Remove-ItemWithRetry -Path $cache.FullName
}

Write-Log "Destroying Python build caches (.pytest_cache, .coverage)..." "INFO"
Remove-ItemWithRetry -Path "$PSScriptRoot\.pytest_cache"
Remove-ItemWithRetry -Path "$PSScriptRoot\.coverage"

Write-Log "Destroying React Vite cache..." "INFO"
Remove-ItemWithRetry -Path "$PSScriptRoot\frontend\node_modules\.vite"

Write-Log "[3/3] System Validation Check..." "INFO"
if (Test-Path "$PSScriptRoot\frontend\node_modules\.vite") {
    Write-Log "Vite cache deletion failed. Manual intervention may be required." "WARN"
}

Write-Log "=======================================================" "SUCCESS"
Write-Log "SYSTEM PURGE COMPLETE" "SUCCESS"
Write-Log "All databases, queues, and caches have been annihilated." "SUCCESS"
Write-Log "=======================================================" "SUCCESS"
