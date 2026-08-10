Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "🚀 Launching OmniModel Universal AI Gateway (Antigravity 2026)..." -ForegroundColor Green
Write-Host "📡 OpenAI Proxy: http://127.0.0.1:8000/v1" -ForegroundColor Yellow
Write-Host "🌐 Web Dashboard: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
python server.py
