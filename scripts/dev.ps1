# ProspectOS dev launcher (Windows/PowerShell)
#
# Starts the backend (FastAPI/uvicorn, http://localhost:8000) and the
# frontend (Next.js, http://localhost:3000) as hidden background processes
# -- no separate CMD/PowerShell windows pop up, everything stays out of
# your way in whatever terminal (including VS Code's integrated one) you
# ran this from. Logs go to .devlogs\backend.log and .devlogs\frontend.log;
# both process IDs are tracked in .dev-pids.json so dev-stop.ps1 can shut
# them down cleanly.
#
# Usage:
#   .\scripts\dev.ps1          # start both
#   .\scripts\dev-stop.ps1     # stop both
#
# Prerequisites (one-time):
#   cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
#   cd frontend; npm install

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".dev-pids.json"
$logDir = Join-Path $root ".devlogs"

function Test-PortInUse($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

if (Test-Path $pidFile) {
    Write-Host "A .dev-pids.json already exists -- dev servers may already be running." -ForegroundColor Yellow
    Write-Host "Run .\scripts\dev-stop.ps1 first if you want to restart them cleanly." -ForegroundColor Yellow
    exit 1
}
if ((Test-PortInUse 8000) -or (Test-PortInUse 3000)) {
    Write-Host "Port 8000 or 3000 is already in use by something outside this script." -ForegroundColor Yellow
    Write-Host "Run .\scripts\dev-stop.ps1 to clean up tracked processes, or free the port(s) manually, then try again." -ForegroundColor Yellow
    exit 1
}

$backendVenvPython = Join-Path $root "backend\.venv\Scripts\python.exe"
$frontendNodeModules = Join-Path $root "frontend\node_modules"

if (-not (Test-Path $backendVenvPython)) {
    Write-Host "Backend virtualenv not found at backend\.venv -- create it first:" -ForegroundColor Yellow
    Write-Host "  cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "Frontend dependencies not installed -- run first:" -ForegroundColor Yellow
    Write-Host "  cd frontend; npm install"
    exit 1
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$backendLog = Join-Path $logDir "backend.log"
$frontendLog = Join-Path $logDir "frontend.log"

# Deliberately NOT using --reload: on Windows, uvicorn's reload worker
# respawns using the venv's *base* interpreter (from pyvenv.cfg) instead of
# the venv itself, silently running the app without any installed packages
# (playwright, bs4, ...) -- every endpoint that touches those 500s while
# simple CRUD keeps working, which is exceptionally confusing to debug.
# Restart the backend (dev-stop.ps1 then dev.ps1) after backend code changes.
$backendCmd = "Set-Location `"$root\backend`"; & `"$backendVenvPython`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 *>> `"$backendLog`""
$frontendCmd = "Set-Location `"$root\frontend`"; npm run dev *>> `"$frontendLog`""

Write-Host "Starting backend  -> http://localhost:8000  (docs at /docs)" -ForegroundColor Cyan
$backendProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", $backendCmd -PassThru

Write-Host "Starting frontend -> http://localhost:3000" -ForegroundColor Cyan
$frontendProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", $frontendCmd -PassThru

@{
    backend  = $backendProc.Id
    frontend = $frontendProc.Id
    started  = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content -Path $pidFile -Encoding utf8

Write-Host ""
Write-Host "Both dev servers are running hidden (no popup windows), tracked in .dev-pids.json."
Write-Host "Tail logs:  Get-Content -Wait .devlogs\backend.log   /   Get-Content -Wait .devlogs\frontend.log"
Write-Host "Stop both:  .\scripts\dev-stop.ps1"
