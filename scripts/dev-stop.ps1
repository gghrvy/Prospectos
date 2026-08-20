# ProspectOS dev stopper (Windows/PowerShell)
#
# Stops whatever `scripts\dev.ps1` started, using the PIDs it recorded in
# .dev-pids.json (tree-killed with taskkill so uvicorn's/npm's child
# processes die too, not just the wrapper window). Falls back to killing
# whatever is listening on 8000/3000 if the PID file is missing or stale,
# so this is also the right tool to reach for when a dev server is stuck.
#
# Usage:
#   .\scripts\dev-stop.ps1

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".dev-pids.json"

function Stop-Tree($processId, $label) {
    if (-not $processId) { return }
    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host "$label (PID $processId) is not running." -ForegroundColor DarkGray
        return
    }
    Write-Host "Stopping $label (PID $processId)..." -ForegroundColor Cyan
    & taskkill /PID $processId /T /F 2>&1 | Out-Null
}

function Stop-Port($port, $label) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        Write-Host "Stopping whatever is on port $port ($label, PID $($conn.OwningProcess))..." -ForegroundColor Cyan
        & taskkill /PID $conn.OwningProcess /T /F 2>&1 | Out-Null
    }
}

if (Test-Path $pidFile) {
    $state = Get-Content $pidFile -Raw | ConvertFrom-Json
    Stop-Tree $state.backend "backend"
    Stop-Tree $state.frontend "frontend"
    Remove-Item $pidFile -Force
} else {
    Write-Host "No .dev-pids.json found -- falling back to killing whatever owns ports 8000/3000." -ForegroundColor Yellow
}

# Always double-check the ports themselves, in case something's listening
# that the PID file didn't know about (e.g. started outside this script).
Start-Sleep -Milliseconds 500
Stop-Port 8000 "backend port"
Stop-Port 3000 "frontend port"

Write-Host "Done."
