@echo off
echo ===================================================================
echo [FreeLLMAPI] Configuring Claude Code for FreeLLMAPI Unified Pool
echo Pools: Google, Groq, Cerebras, Mistral, OpenRouter (~10.1B tokens/mo)
echo ===================================================================
npx --yes freellmapi setup-claude --url http://localhost:3001
