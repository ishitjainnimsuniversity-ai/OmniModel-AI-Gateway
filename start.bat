@echo off
title OmniModel Universal AI Gateway
cd /d "%~dp0"
echo ====================================================================
echo 🚀 Starting OmniModel Universal AI Gateway (2026 Edition)...
echo 📡 OpenAI Drop-in Proxy: http://127.0.0.1:8000/v1
echo 🌐 Web Dashboard and Arena: http://127.0.0.1:8000/
echo ====================================================================
python server.py
pause
