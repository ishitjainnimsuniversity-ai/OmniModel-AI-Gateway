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
            # Map legacy/alias Gemini model IDs to live Gemini 3.5/3.8 models on user's key
            if model in ("gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-1.5-flash"):
                model = "gemini-3.5-flash-lite"
            elif "thinking" in model or model in ("gemini-2.0-flash-thinking", "gemini-2.5-pro", "gemini-1.5-pro"):
                model = "gemini-3.8-flash"
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
            ollama_base = (os.getenv("OLLAMA_BASE_URL") or "").strip() or "http://localhost:11434"
            target_url = f"{ollama_base}/v1/chat/completions"
            return target_url, headers, format_type

        elif provider_id == "pollinations":
            target_url = "https://text.pollinations.ai/openai"
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
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        api_key_override: Optional[str] = None,
        session_keys: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields normalized streaming SSE chunks:
        {"delta": "text", "done": bool, "provider": str, "model": str, "latency_ms": float, "tokens": int}
        """
        start_time = time.perf_counter()
        meta = PROVIDERS_METADATA.get(provider_id)
        if not meta:
            yield {"delta": f"[Error: Unknown provider '{provider_id}']", "content": f"[Error: Unknown provider '{provider_id}']", "done": True, "error": True}
            return

        env_var = meta.get("env_var")
        s_keys = session_keys or {}
        api_key = (
            api_key_override
            or (s_keys.get(env_var) if env_var else None)
            or (GatewayConfig.get_key(env_var) if env_var else None)
        )

        if provider_id == "openrouter" and (not model or model.endswith(":free")):
            model = "openrouter/free"

        # If a specific provider's key is not set in .env, seamlessly bridge through active OPENROUTER_API_KEY or GEMINI_API_KEY
        if provider_id not in ("ollama", "pollinations") and not api_key:
            or_key = s_keys.get("OPENROUTER_API_KEY") or GatewayConfig.get_key("OPENROUTER_API_KEY")
            gem_key = s_keys.get("GEMINI_API_KEY") or GatewayConfig.get_key("GEMINI_API_KEY")
            if or_key:
                provider_id = "openrouter"
                meta = PROVIDERS_METADATA["openrouter"]
                api_key = or_key
                model = "openrouter/free"
            elif gem_key:
                provider_id = "gemini"
                meta = PROVIDERS_METADATA["gemini"]
                api_key = gem_key
                model = "gemini-3.5-flash-lite"
            else:
                yield {
                    "delta": f"Missing API key for {meta.get('name', provider_id)}",
                    "content": "",
                    "done": True,
                    "error": True,
                    "status": "missing_key",
                    "provider": provider_id,
                    "model": model
                }
                return

        target_url, headers, format_type = cls._prepare_headers_and_url(provider_id, model, api_key)

        async with httpx.AsyncClient(timeout=25.0, verify=False) as client:
            try:
                if format_type == "gemini":
                    # Convert to Gemini format (with optional Vision inlineData support)
                    gemini_contents = []
                    system_instruction = None
                    for m in messages:
                        role = m.get("role", "user")
                        content = m.get("content", "")
                        if role == "system":
                            system_instruction = {"parts": [{"text": content}]}
                        else:
                            gem_role = "user" if role == "user" else "model"
                            parts: List[Dict[str, Any]] = [{"text": content}]
                            for img in (m.get("images") or []):
                                b64_data = img.get("data", "")
                                mime = img.get("mime_type", "image/jpeg")
                                if b64_data:
                                    parts.append({"inlineData": {"mimeType": mime, "data": b64_data}})
                            gemini_contents.append({"role": gem_role, "parts": parts})

                    payload = {
                        "contents": gemini_contents,
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max(max_tokens or 1024, 1024)
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
                                    "content": chunk_text,
                                    "done": False,
                                    "provider": provider_id,
                                    "model": model,
                                    "latency_ms": latency
                                }
                            yield {
                                "delta": "",
                                "content": "",
                                "done": True,
                                "provider": provider_id,
                                "model": model,
                                "latency_ms": latency,
                                "total_chars": len(full_text)
                            }
                        else:
                            yield {"delta": "No output generated.", "content": "No output generated.", "done": True, "provider": provider_id, "model": model}
                    else:
                        err_text = f"Gemini API Error ({response.status_code}): {response.text}"
                        yield {
                            "delta": err_text,
                            "content": err_text,
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

                elif provider_id == "pollinations":
                    clean_msgs = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]
                    payload = {
                        "model": model or "openai",
                        "messages": clean_msgs,
                        "temperature": temperature,
                        "stream": False
                    }
                    response = await client.post(target_url, headers=headers, json=payload, timeout=7.5)
                    latency = round((time.perf_counter() - start_time) * 1000, 2)
                    full_text = ""
                    rate_limited = response.status_code in (402, 429, 502, 503)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            full_text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                        except Exception:
                            full_text = response.text.strip()
                    if full_text and ("Free limit reached" in full_text or "enter.pollinations.ai" in full_text):
                        full_text = ""
                        rate_limited = True
                    if not full_text and not rate_limited:
                        import urllib.parse
                        last_q = clean_msgs[-1].get("content", "Hello") if clean_msgs else "Hello"
                        r_get = await client.get(f"https://text.pollinations.ai/{urllib.parse.quote(last_q[:400])}", timeout=5.5)
                        if r_get.status_code == 200:
                            cand = r_get.text.strip()
                            if cand and "Free limit reached" not in cand and "enter.pollinations.ai" not in cand:
                                full_text = cand

                    if full_text and len(full_text.strip()) > 0:
                        words = full_text.split(" ")
                        for i, w in enumerate(words):
                            chunk_text = w + (" " if i < len(words) - 1 else "")
                            yield {
                                "delta": chunk_text,
                                "content": chunk_text,
                                "done": False,
                                "provider": "pollinations",
                                "model": model or "openai",
                                "latency_ms": latency
                            }
                        yield {
                            "delta": "",
                            "content": "",
                            "done": True,
                            "provider": "pollinations",
                            "model": model or "openai",
                            "latency_ms": latency
                        }
                    else:
                        yield {"delta": "Pollinations unavailable", "done": True, "error": True, "provider": "pollinations", "model": model}

                else:
                    # Standard OpenAI Compatible streaming or non-streaming (supports optional images)
                    formatted_messages: List[Dict[str, Any]] = []
                    for m in messages:
                        imgs = m.get("images") or []
                        if imgs:
                            c_parts: List[Dict[str, Any]] = [{"type": "text", "text": m.get("content", "")}]
                            for img in imgs:
                                b64_data = img.get("data", "")
                                mime = img.get("mime_type", "image/jpeg")
                                if b64_data:
                                    c_parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_data}"}})
                            formatted_messages.append({"role": m.get("role", "user"), "content": c_parts})
                        else:
                            formatted_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

                    payload = {
                        "model": model,
                        "messages": formatted_messages,
                        "temperature": temperature,
                        "stream": True
                    }
                    if provider_id == "openrouter":
                        payload["reasoning"] = {"exclude": True}
                    elif max_tokens:
                        payload["max_tokens"] = max_tokens

                    # Attempt streaming request
                    try:
                        async with client.stream("POST", target_url, headers=headers, json=payload, timeout=22.0) as resp:
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
                                            content = delta.get("content", "")
                                            if content:
                                                yield {
                                                    "delta": content,
                                                    "content": content,
                                                    "done": False,
                                                    "provider": provider_id,
                                                    "model": model,
                                                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
                                                }
                                    except Exception:
                                        pass

                            yield {
                                "delta": "",
                                "content": "",
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
                            yield {"delta": content, "content": content, "done": True, "provider": provider_id, "model": model, "latency_ms": latency}
                        else:
                            err_msg = f"API Error: {resp.text}"
                            yield {"delta": err_msg, "content": err_msg, "done": True, "error": True, "provider": provider_id}

            except Exception as e:
                err_msg = f"\n[Connection Exception on {provider_id} ({model})]: {str(e)}"
                yield {
                    "delta": err_msg,
                    "content": err_msg,
                    "done": True,
                    "error": True,
                    "provider": provider_id,
                    "model": model,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
                }

    @classmethod
    async def test_ping(cls, provider_id: str, api_key_override: Optional[str] = None) -> Dict[str, Any]:
        """Pings provider endpoint to test authentication and latency"""
        start = time.perf_counter()
        meta = PROVIDERS_METADATA.get(provider_id)
        if not meta:
            return {"provider": provider_id, "status": "unknown", "latency_ms": 0, "message": "Unknown provider"}

        env_var = meta.get("env_var")
        api_key = api_key_override or (GatewayConfig.get_key(env_var) if env_var else None)

        if provider_id == "ollama":
            # Test local ollama
            try:
                async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
                    resp = await client.get("http://localhost:11434/api/tags")
                    latency = round((time.perf_counter() - start) * 1000, 2)
                    if resp.status_code == 200:
                        return {"provider": provider_id, "status": "active", "latency_ms": latency, "message": "Local Ollama running"}
                    return {"provider": provider_id, "status": "offline", "latency_ms": latency, "message": "Ollama not running locally"}
            except Exception as e:
                return {"provider": provider_id, "status": "offline", "latency_ms": 0, "message": "Ollama offline"}

        if provider_id == "pollinations":
            try:
                async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                    resp = await client.post(
                        "https://text.pollinations.ai/openai",
                        json={"model": "openai", "messages": [{"role": "user", "content": "OK"}], "stream": False}
                    )
                    latency = round((time.perf_counter() - start) * 1000, 2)
                    if resp.status_code == 200:
                        return {"provider": provider_id, "status": "active", "latency_ms": latency, "message": "Connected successfully (Keyless Cloud)"}
                    if resp.status_code in (402, 429):
                        return {"provider": provider_id, "status": "rate_limited", "latency_ms": latency, "message": "45s shared-IP cooldown; Live Knowledge Engine active"}
                    return {"provider": provider_id, "status": "error", "latency_ms": latency, "message": f"HTTP {resp.status_code}"}
            except Exception as e:
                return {"provider": provider_id, "status": "error", "latency_ms": 0, "message": str(e)}

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
                max_tokens=10,
                api_key_override=api_key_override
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
