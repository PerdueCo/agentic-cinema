Write-Host "Agentic Studio Digital Twin Demo" -ForegroundColor Cyan
Write-Host "This opens two PowerShell windows: FastAPI backend and React frontend." -ForegroundColor Gray

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backend'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; python -m uvicorn app.main:app --reload --port 8000"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontend'; npm install; npm run dev"

Write-Host "Backend starting on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend normally starts on http://localhost:5173" -ForegroundColor Green
