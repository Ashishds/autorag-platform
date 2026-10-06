# AutoRAG Local Runner (Without Docker)
# Starts Redis (Memurai check), Backend FastAPI, Celery Worker, and Frontend Next.js

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   AutoRAG Local Runner (No Docker)                 " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Check Redis
$redisCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 6379 -WarningAction SilentlyContinue
if (-not $redisCheck.TcpTestSucceeded) {
    Write-Warning "Redis (port 6379) is not running! Starting Memurai..."
    Start-Service -Name Memurai -ErrorAction SilentlyContinue
} else {
    Write-Host "[OK] Redis is active on port 6379" -ForegroundColor Green
}

# 2. Launch Backend API
Write-Host "Launching Backend API (http://localhost:8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\backend'; Write-Host '--- AutoRAG Backend API ---' -ForegroundColor Cyan; uv run uvicorn app.main:app --reload --port 8000"

# 3. Launch Celery Worker (requires --pool=solo on Windows)
Write-Host "Launching Celery Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\backend'; Write-Host '--- AutoRAG Celery Worker ---' -ForegroundColor Cyan; uv run celery -A app.workers.celery_app.celery worker --loglevel=info --pool=solo"

# 4. Launch Frontend Dev Server
Write-Host "Launching Frontend Dev Server (http://localhost:3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\frontend'; Write-Host '--- AutoRAG Frontend Next.js ---' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "All services launched in separate windows!" -ForegroundColor Green
Write-Host "API:      http://localhost:8000 (Docs at /docs, Health at /health)"
Write-Host "Frontend: http://localhost:3000"
Write-Host "=====================================================" -ForegroundColor Cyan
