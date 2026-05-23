$root = $PSScriptRoot

Write-Host "========================================"
Write-Host "  Agentic AI Platform - Starting Up"
Write-Host "========================================"

# Start backend in a new PowerShell window
Write-Host "[1/2] Starting backend on port 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
  Set-Location '$root'
  Write-Host 'Activating virtual environment...'
  .\venv\Scripts\Activate.ps1
  Set-Location backend
  Write-Host 'Starting uvicorn...'
  uvicorn api.main:app --reload --port 8000
"@

Start-Sleep -Seconds 2

# Start frontend in a new PowerShell window
Write-Host "[2/2] Starting frontend on port 3000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
  Set-Location '$root\frontend'
  Write-Host 'Starting frontend dev server...'
  npm run dev
"@

Write-Host ""
Write-Host "========================================"
Write-Host "  Backend  -> http://localhost:8000"
Write-Host "  Frontend -> http://localhost:3000"
Write-Host "  API Docs -> http://localhost:8000/docs"
Write-Host "========================================"
Write-Host "  Close the terminal windows to stop."
Write-Host "========================================"
