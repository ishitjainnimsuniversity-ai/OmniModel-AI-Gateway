"""
Universal Provider Adapters for OmniModel Gateway
Supports all 20 AI Providers with streaming, standard OpenAI compatibility, and fallback error handling.
"""

import json
import os
import time
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from core.config import GatewayConfig
from core.providers import PROVIDERS_METADATA

class UniversalAdapter:
    @staticmethod
    def _prepare_headers_and_url(provider_id: str, model: str, api_key: Optional[str]) -> Tuple[str, Dict[str, str], str]:
        meta = PROVIDERS_METADATA.get(provider_id, {})
        base_url = meta.get("base_url", "")
        format_type = meta.get("format_type", "openai_compatible")

        headers = {
            "Content-Type": "application/json"
        }

        if provider_id == "gemini":
            # Gemini REST API
            target_url = f"{base_url}/models/{model}:generateContent?key={api_key or ''}"
            return target_url, headers, format_type

        elif provider_id == "anthropic":
            target_url = f"{base_url}/messages"
            headers["x-api-key"] = api_key or ""
            headers["anthropic-version"] = "2023-06-01"
            return target_url, headers, format_type

        elif provider_id == "cohere":
            target_url = f"{base_url}/chat"
            headers["Authorization"] = f"Bearer {api_key or ''}"
            return target_url, headers, format_type

        elif provider_id == "openrouter":
            target_url = f"{base_url}/chat/completions"
            headers["Authorization"] = f"Bearer {api_key or ''}"
            headers["HTTP-Referer"] = "https://github.com/google/antigravity"
            headers["X-Title"] = "OmniModel AI Gateway"
            return target_url, headers, format_type

        elif provider_id == "ollama":
            # Local Ollama default
            ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            target_url = f"{ollama_base}/v1/chat/completions"
            return target_url, headers, format_type

        else:
            # Standard OpenAI-compatible endpoints (Groq, DeepSeek, Cerebras, SambaNova, Together, Fireworks, Perplexity, xAI, Mistral, OpenAI, HuggingFace, AI21)
            target_url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return target_url, headers, format_type

    @classmethod
    async def chat_stream(
        cls,
        provider_id: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields normalized streaming SSE chunks:
        {"delta": "text", "done": bool, "provider": str, "model": str, "latency_ms": float, "tokens": int}
        """
        start_time = time.perf_counter()
        meta = PROVIDERS_METADATA.get(provider_id)
        if not meta:
            yield {"delta": f"[Error: Unknown provider '{provider_id}']", "done": True, "error": True}
            return

        env_var = meta.get("env_var")
        api_key = GatewayConfig.get_key(env_var) if env_var else None

        # Check if key is required and missing
        if provider_id != "ollama" and not api_key:
            # Yield simulated fallback / key missing advice
            free_url = meta.get("free_key_url", "https://ai.google.dev/")
            missing_msg = (
                f"\n\n⚡ **[Provider Notice: {meta['name']}]**\n"
                f"No API key detected in `.env` for `{env_var}`.\n"
                f"- **Free Tier**: {meta.get('free_tier_note', 'Available')}\n"
                f"- **Get API Key**: [{free_url}]({free_url})\n\n"
                f"*To connect live: configure your key in the dashboard or in `.env`.*"
            )
            yield {
                "delta": missing_msg,
                "done": True,
                "provider": provider_id,
                "model": model,
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "error": True,
                "status": "missing_key"
            }
            return

        target_url, headers, format_type = cls._prepare_headers_and_url(provider_id, model, api_key)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                if format_type == "gemini":
                    # Convert to Gemini format
                    gemini_contents = []
                    system_instruction = None
                    for m in messages:
                        role = m.get("role", "user")
                        content = m.get("content", "")
                        if role == "system":
                            system_instruction = {"parts": [{"text": content}]}
                        else:
                            gem_role = "user" if role == "user" else "model"
                            gemini_contents.append({"role": gem_role, "parts": [{"text": content}]})

                    payload = {
                        "contents": gemini_contents,
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens
                        }
                    }
                    if system_instruction:
                        payload["systemInstruction"] = system_instruction

                    # Call Gemini
                    response = await client.post(target_url, headers=headers, json=payload)
                    latency = round((time.perf_counter() - start_time) * 1000, 2)
                    
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_chunks = [p.get("text", "") for p in parts]
                            full_text = "".join(text_chunks)
                            # Yield in small bursts for realistic streaming feel
                            words = full_text.split(" ")
                            for i, w in enumerate(words):
                                chunk_text = w + (" " if i < len(words) - 1 else "")
                                yield {
                                    "delta": chunk_text,
                                    "done": False,
                                    "provider": provider_id,
                                    "model": model,
                                    "latency_ms": latency
                                }
                            yield {
                                "delta": "",
                                "done": True,
                                "provider": provider_id,
                                "model": model,
                                "latency_ms": latency,
                                "total_chars": len(full_text)
                            }
                        else:
                            yield {"delta": "No output generated.", "done": True, "provider": provider_id, "model": model}
                    else:
                        yield {
                            "delta": f"Gemini API Error ({response.status_code}): {response.text}",
                            "done": True,
                            "error": True,
                            "provider": provider_id,
                            "model": model
                        }

                elif format_type == "anthropic":
                    # Convert to Anthropic format
                    claude_messages = []
                    system_prompt = ""
                    for m in messages:
                        role = m.get("role", "user")
                        content = m.get("content", "")
                        if role == "system":
                            system_prompt = content
                        else:
                            claude_messages.append({"role": role, "content": content})

                    payload = {
                        "model": model,
                        "messages": claude_messages,
                        "max_tokens": max_tokens or 2048,
                        "temperature": temperature
                    }
                    if system_prompt:
                        payload["system"] = system_prompt

                    response = await client.post(target_url, headers=headers, json=payload)
                    latency = round((time.perf_counter() - start_time) * 1000, 2)

                    if response.status_code == 200:
                        data = response.json()
                        content_blocks = data.get("content", [])
                        full_text = "".join([c.get("text", "") for c in content_blocks if c.get("type") == "text"])
                        words = full_text.split(" ")
                        for i, w in enumerate(words):
                            chunk_text = w + (" " if i < len(words) - 1 else "")
                            yield {
                                "delta": chunk_text,
                                "done": False,
                                "provider": provider_id,
                                "model": model,
                                "latency_ms": latency
                            }
                        yield {
                            "delta": "",
                            "done": True,
                            "provider": provider_id,
                            "model": model,
                            "latency_ms": latency
                        }
                    else:
                        yield {
                            "delta": f"Anthropic API Error ({response.status_code}): {response.text}",
                            "done": True,
                            "error": True,
                            "provider": provider_id,
                            "model": model
                        }

                elif format_type == "cohere":
                    # Cohere Chat API v2
                    payload = {
                        "model": model,
                        "messages": [{"role": m.get("role", "user"), "content": {"type": "text", "text": m.get("content", "")}} for m in messages]
                    }
                    response = await client.post(target_url, headers=headers, json=payload)
                    latency = round((time.perf_counter() - start_time) * 1000, 2)
                    if response.status_code == 200:
                        data = response.json()
                        message_content = data.get("message", {}).get("content", [])
                        full_text = "".join([c.get("text", "") for c in message_content if isinstance(c, dict)])
                        yield {"delta": full_text, "done": True, "provider": provider_id, "model": model, "latency_ms": latency}
                    else:
                        yield {"delta": f"Cohere Error ({response.status_code}): {response.text}", "done": True, "error": True}

                else:
                    # Standard OpenAI Compatible streaming or non-streaming
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True
                    }

                    # Attempt streaming request
                    try:
                        async with client.stream("POST", target_url, headers=headers, json=payload, timeout=60.0) as resp:
                            if resp.status_code != 200:
                                error_body = await resp.aread()
                                yield {
                                    "delta": f"Provider Error ({resp.status_code}): {error_body.decode('utf-8', errors='ignore')}",
                                    "done": True,
                                    "error": True,
                                    "provider": provider_id,
                                    "model": model
                                }
                                return

                            async for line in resp.aiter_lines():
                                if not line:
                                    continue
                                line = line.strip()
                                if line.startswith("data: "):
                                    data_str = line[6:]
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        chunk_json = json.loads(data_str)
                                        choices = chunk_json.get("choices", [])
                                        if choices:
                                            delta = choices[0].get("delta", {})
                                            content = delta.get("content", "") or delta.get("reasoning_content", "")
                                            if content:
                                                yield {
                                                    "delta": content,
                                                    "done": False,
                                                    "provider": provider_id,
                                                    "model": model,
                                                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
                                                }
                                    except Exception:
                                        pass

                            yield {
                                "delta": "",
                                "done": True,
                                "provider": provider_id,
                                "model": model,
                                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
                            }
                    except Exception as stream_err:
                        # Fallback to non-streaming if stream not supported
                        payload["stream"] = False
                        resp = await client.post(target_url, headers=headers, json=payload)
                        latency = round((time.perf_counter() - start_time) * 1000, 2)
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            yield {"delta": content, "done": True, "provider": provider_id, "model": model, "latency_ms": latency}
                        else:
                            yield {"delta": f"API Error: {resp.text}", "done": True, "error": True, "provider": provider_id}

            except Exception as e:
                yield {
                    "delta": f"\n[Connection Exception on {provider_id} ({model})]: {str(e)}",
                    "done": True,
                    "error": True,
                    "provider": provider_id,
                    "model": model,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
                }

    @classmethod
    async def test_ping(cls, provider_id: str) -> Dict[str, Any]:
        """Pings provider endpoint to test authentication and latency"""
        start = time.perf_counter()
        meta = PROVIDERS_METADATA.get(provider_id)
        if not meta:
            return {"provider": provider_id, "status": "unknown", "latency_ms": 0, "message": "Unknown provider"}

        env_var = meta.get("env_var")
        api_key = GatewayConfig.get_key(env_var) if env_var else None

        if provider_id == "ollama":
            # Test local ollama
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get("http://localhost:11434/api/tags")
                    latency = round((time.perf_counter() - start) * 1000, 2)
                    if resp.status_code == 200:
                        return {"provider": provider_id, "status": "active", "latency_ms": latency, "message": "Local Ollama running"}
                    return {"provider": provider_id, "status": "offline", "latency_ms": latency, "message": "Ollama not running locally"}
            except Exception as e:
                return {"provider": provider_id, "status": "offline", "latency_ms": 0, "message": "Ollama offline"}

        if not api_key:
            return {
                "provider": provider_id,
                "status": "missing_key",
                "latency_ms": 0,
                "message": f"Missing {env_var} in .env",
                "free_tier": meta.get("free_tier_available", False),
                "free_url": meta.get("free_key_url", "")
            }

        # Quick test chat
        try:
            model = meta.get("default_model")
            async for chunk in cls.chat_stream(
                provider_id=provider_id,
                model=model,
                messages=[{"role": "user", "content": "Reply with 'OK'."}],
                max_tokens=10
            ):
                if chunk.get("error"):
                    return {
                        "provider": provider_id,
                        "status": "auth_error",
                        "latency_ms": chunk.get("latency_ms", 0),
                        "message": chunk.get("delta", "Authentication or quota error")
                    }
            latency = round((time.perf_counter() - start) * 1000, 2)
            return {"provider": provider_id, "status": "active", "latency_ms": latency, "message": "Connected successfully"}
        except Exception as e:
            return {"provider": provider_id, "status": "error", "latency_ms": 0, "message": str(e)}
