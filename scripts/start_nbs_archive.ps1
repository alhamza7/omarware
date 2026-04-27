# Start NBS Archive System
# Starts both Odoo backend and React frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NBS Archive System - Startup Script  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Odoo is already running
$odooProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*Lugal-ai*"}
if ($odooProcess) {
    Write-Host "Odoo is already running (PID: $($odooProcess.Id))" -ForegroundColor Yellow
    Stop-Process -Id $odooProcess.Id -Force
    Write-Host "Stopped existing Odoo process" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Check if Frontend is already running
$frontendProcess = Get-Process node -ErrorAction SilentlyContinue
if ($frontendProcess) {
    Write-Host "Frontend is already running" -ForegroundColor Yellow
    Stop-Process -Name node -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped existing Frontend process" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Start Odoo Backend
Write-Host ""
Write-Host "Starting Odoo Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd 'D:\capo_dev\Lugal-ai'; Write-Host '=== Odoo Backend ===' -ForegroundColor Green; Write-Host ''; .\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal"

Write-Host "Waiting for Odoo to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Start React Frontend
Write-Host ""
Write-Host "Starting React Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd 'D:\capo_dev\Lugal-ai\frontend'; Write-Host '=== React Frontend ===' -ForegroundColor Cyan; Write-Host ''; npm run dev"

Write-Host "Waiting for Frontend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Display status
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  NBS Archive System Started!          " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  * Odoo Backend:   http://localhost:8070" -ForegroundColor White
Write-Host "  * React Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  * PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "Login credentials:" -ForegroundColor Yellow
Write-Host "  * Username: admin" -ForegroundColor White
Write-Host "  * Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "Open in browser: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
