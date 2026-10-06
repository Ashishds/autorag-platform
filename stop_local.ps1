# Stop AutoRAG Local Dev Processes

Write-Host "Stopping AutoRAG local dev processes..." -ForegroundColor Yellow

# Stop Uvicorn / Python processes running app.main
Get-CimInstance Win32_Process | Where-Object { 
    $_.CommandLine -like "*uvicorn app.main:app*" -or 
    $_.CommandLine -like "*celery -A app.workers.celery_app*" 
} | ForEach-Object {
    Write-Host "Stopping Process ID: $($_.ProcessId) ($($_.Name))" -ForegroundColor Cyan
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# Stop Next.js dev server on port 3000 if running
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    $pids = $port3000 | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $pids) {
        if ($p -gt 0) {
            Write-Host "Stopping frontend process on port 3000 (PID: $p)..." -ForegroundColor Cyan
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "AutoRAG processes stopped." -ForegroundColor Green
