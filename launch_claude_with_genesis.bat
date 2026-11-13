@echo off
echo ===================================================================
echo [GENESIS AI 5.0] Launching Claude Code with Infinite Free Tier Routing
echo Target Gateway: http://localhost:8000 (OmniModel Universal Gateway)
echo Auto-Fallback: Gemini, Groq, OpenRouter Free, Cerebras, Pollinations
echo ===================================================================
set ANTHROPIC_BASE_URL=http://localhost:8000
set ANTHROPIC_AUTH_TOKEN=genesis-free-tier
claude %*
