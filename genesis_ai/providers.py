"""Cloud AI providers: Gemini (native REST) and OpenAI-compatible (OpenAI, OpenRouter, Groq, DeepSeek).

Request formats follow the providers' public REST docs. TLS certificates are always verified.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional

import httpx

from .errors import (AuthError, BadRequest, EmptyResponse, ModelUnavailable, NetworkError,
                     NotConfigured, ProviderError, RateLimited, UpstreamError, UpstreamTimeout)
from .settings import PROVIDER_SPECS, get_secret, settings

Message = Dict[str, str]  # {"role": "system"|"user"|"assistant", "content": "..."}


@dataclass
class GenResult:
    text: str
    provider: str
    model: str
    latency_s: float
    sources: List[Dict[str, str]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)


def _retry_after(resp: httpx.Response) -> Optional[float]:
    try:
        return float(resp.headers.get("retry-after", ""))
    except ValueError:
        return None


def _raise_for_status(provider: str, resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return
    try:
        detail = resp.json()
        msg = (detail.get("error") or {}).get("message") or str(detail)
    except Exception:
        msg = resp.text
    msg = (msg or "").replace("\n", " ")[:300]
    s = resp.status_code
    if s in (401, 403) or (s == 400 and "API_KEY" in msg.upper()):
        raise AuthError(f"Credentials rejected: {msg}", provider, s)
    if s == 429:
        raise RateLimited(f"Rate limit or quota exceeded: {msg}", provider, s, _retry_after(resp))
    if s == 404:
        raise ModelUnavailable(f"Model or endpoint not available: {msg}", provider, s)
    if s in (400, 422):
        raise BadRequest(msg, provider, s)
    if s >= 500 or s in (408, 409):
        raise UpstreamError(f"Provider server error {s}: {msg}", provider, s)
    raise ProviderError(f"HTTP {s}: {msg}", provider, s)


class BaseProvider:
    id = ""

    def __init__(self) -> None:
        spec = PROVIDER_SPECS[self.id]
        self.base = spec["base"] or ""
        self.env_name = spec["env"] or ""

    @property
    def key(self) -> Optional[str]:
        return get_secret(self.env_name)

    @property
    def configured(self) -> bool:
        return bool(self.key)

    def _need_key(self) -> str:
        k = self.key
        if not k:
            raise NotConfigured(f"{self.env_name} is not set in the backend .env", self.id)
        return k

    async def generate(self, messages: List[Message], model: str, *, temperature: float = 0.6,
                       max_tokens: Optional[int] = None, grounding: bool = False) -> GenResult:
        raise NotImplementedError

    async def stream(self, messages: List[Message], model: str, *, temperature: float = 0.6,
                     max_tokens: Optional[int] = None) -> AsyncIterator[str]:
        raise NotImplementedError
        yield ""  # pragma: no cover

    async def list_models(self) -> List[str]:
        return []

    def _client(self) -> httpx.AsyncClient:
        t = settings.request_timeout
        return httpx.AsyncClient(timeout=httpx.Timeout(t, connect=10.0), verify=True)


# ----------------------------------------------------------------------------- Gemini
class GeminiProvider(BaseProvider):
    id = "gemini"

    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": self._need_key(), "Content-Type": "application/json"}

    @staticmethod
    def _body(messages: List[Message], temperature: float, max_tokens: Optional[int],
              grounding: bool) -> dict:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        body: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or settings.max_output_tokens,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if grounding:
            body["tools"] = [{"google_search": {}}]
        return body

    @staticmethod
    def _extract(data: dict) -> tuple[str, List[Dict[str, str]]]:
        cands = data.get("candidates") or []
        if not cands:
            fb = (data.get("promptFeedback") or {}).get("blockReason")
            raise EmptyResponse(f"No candidates returned{' (blocked: ' + fb + ')' if fb else ''}",
                                "gemini")
        cand = cands[0]
        parts = (cand.get("content") or {}).get("parts") or []
        # Skip "thought" parts; only return the final answer text.
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        sources = []
        for ch in (cand.get("groundingMetadata") or {}).get("groundingChunks", []):
            w = ch.get("web") or {}
            if w.get("uri"):
                sources.append({"title": w.get("title", ""), "url": w["uri"]})
        return text.strip(), sources

    async def generate(self, messages, model, *, temperature=0.6, max_tokens=None, grounding=False):
        url = f"{self.base}/models/{model}:generateContent"
        t0 = time.monotonic()
        try:
            async with self._client() as c:
                r = await c.post(url, headers=self._headers(),
                                 json=self._body(messages, temperature, max_tokens, grounding))
        except httpx.TimeoutException as e:
            raise UpstreamTimeout(f"Timed out after {settings.request_timeout:.0f}s", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        _raise_for_status(self.id, r)
        data = r.json()
        text, sources = self._extract(data)
        if not text:
            reason = ((data.get("candidates") or [{}])[0]).get("finishReason", "unknown")
            raise EmptyResponse(f"Model returned no text (finishReason={reason})", self.id)
        usage = data.get("usageMetadata") or {}
        return GenResult(text, self.id, model, time.monotonic() - t0, sources,
                         {"prompt": usage.get("promptTokenCount", 0),
                          "output": usage.get("candidatesTokenCount", 0)})

    async def stream(self, messages, model, *, temperature=0.6, max_tokens=None):
        url = f"{self.base}/models/{model}:streamGenerateContent?alt=sse"
        got_any = False
        try:
            async with self._client() as c:
                async with c.stream("POST", url, headers=self._headers(),
                                    json=self._body(messages, temperature, max_tokens, False)) as r:
                    if r.status_code >= 400:
                        await r.aread()
                        _raise_for_status(self.id, r)
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if not payload:
                            continue
                        try:
                            data = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        try:
                            text, _ = self._extract(data)
                        except EmptyResponse:
                            continue
                        if text:
                            got_any = True
                            yield text
        except httpx.TimeoutException as e:
            raise UpstreamTimeout("Stream timed out", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        if not got_any:
            raise EmptyResponse("Stream ended without text", self.id)

    async def list_models(self) -> List[str]:
        try:
            async with self._client() as c:
                r = await c.get(f"{self.base}/models", headers=self._headers())
            _raise_for_status(self.id, r)
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        return [m["name"].split("/", 1)[-1] for m in r.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])]


# ------------------------------------------------------------- OpenAI-compatible family
class OpenAICompatProvider(BaseProvider):
    """OpenAI, OpenRouter, Groq and DeepSeek share the /chat/completions schema."""

    def __init__(self, provider_id: str) -> None:
        self.id = provider_id
        super().__init__()

    def _headers(self) -> Dict[str, str]:
        h = {"Authorization": f"Bearer {self._need_key()}", "Content-Type": "application/json"}
        if self.id == "openrouter":
            h["X-Title"] = "GENESIS AI"
        return h

    def _body(self, messages, model, temperature, max_tokens, stream) -> dict:
        body = {"model": model, "messages": messages, "temperature": temperature,
                "max_tokens": max_tokens or settings.max_output_tokens, "stream": stream}
        if self.id == "openrouter":
            body["reasoning"] = {"exclude": True}
        return body

    async def generate(self, messages, model, *, temperature=0.6, max_tokens=None, grounding=False):
        t0 = time.monotonic()
        try:
            async with self._client() as c:
                r = await c.post(f"{self.base}/chat/completions", headers=self._headers(),
                                 json=self._body(messages, model, temperature, max_tokens, False))
        except httpx.TimeoutException as e:
            raise UpstreamTimeout(f"Timed out after {settings.request_timeout:.0f}s", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        _raise_for_status(self.id, r)
        data = r.json()
        if data.get("error"):  # OpenRouter can return 200 with an error object
            e = data["error"]
            code = e.get("code")
            msg = str(e.get("message", e))[:300]
            if code == 429:
                raise RateLimited(msg, self.id, 429)
            raise UpstreamError(msg, self.id, code if isinstance(code, int) else None)
        choices = data.get("choices") or []
        text = ((choices[0].get("message") or {}).get("content") or "").strip() if choices else ""
        if not text:
            raise EmptyResponse("Model returned no text", self.id)
        usage = data.get("usage") or {}
        return GenResult(text, self.id, data.get("model") or model, time.monotonic() - t0, [],
                         {"prompt": usage.get("prompt_tokens", 0),
                          "output": usage.get("completion_tokens", 0)})

    async def stream(self, messages, model, *, temperature=0.6, max_tokens=None):
        got_any = False
        try:
            async with self._client() as c:
                async with c.stream("POST", f"{self.base}/chat/completions",
                                    headers=self._headers(),
                                    json=self._body(messages, model, temperature, max_tokens, True)) as r:
                    if r.status_code >= 400:
                        await r.aread()
                        _raise_for_status(self.id, r)
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            delta = json.loads(payload)["choices"][0].get("delta", {}).get("content")
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                        if delta:
                            got_any = True
                            yield delta
        except httpx.TimeoutException as e:
            raise UpstreamTimeout("Stream timed out", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        if not got_any:
            raise EmptyResponse("Stream ended without text", self.id)

    async def list_models(self) -> List[str]:
        try:
            async with self._client() as c:
                r = await c.get(f"{self.base}/models", headers=self._headers())
            _raise_for_status(self.id, r)
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {type(e).__name__}", self.id) from e
        return [m.get("id", "") for m in r.json().get("data", [])]


# ------------------------------------------------------------- Local Ollama Provider
class OllamaProvider(BaseProvider):
    """Local, offline-first Ollama provider running on http://127.0.0.1:11434."""

    id = "ollama"

    def __init__(self) -> None:
        self.base = settings.ollama_base_url
        self.env_name = ""
        self._last_check = 0.0
        self._last_ok = False

    @property
    def key(self) -> Optional[str]:
        return "local_ollama"

    @property
    def configured(self) -> bool:
        """True if Ollama daemon is currently responsive on local port 11434."""
        now = time.monotonic()
        if now - self._last_check < 4.0:
            return self._last_ok
        try:
            # Synchronous light check
            import urllib.request
            req = urllib.request.Request(f"{self.base}/api/tags", headers={"User-Agent": "GENESIS-AI"})
            with urllib.request.urlopen(req, timeout=0.6) as resp:
                self._last_ok = (resp.status == 200)
        except Exception:
            self._last_ok = False
        self._last_check = now
        return self._last_ok

    def _client(self) -> httpx.AsyncClient:
        # Local model inference may take longer on CPU
        t = max(60.0, settings.request_timeout)
        return httpx.AsyncClient(timeout=httpx.Timeout(t, connect=3.0), verify=False)

    async def generate(self, messages: List[Message], model: str, *, temperature: float = 0.6,
                       max_tokens: Optional[int] = None, grounding: bool = False) -> GenResult:
        t0 = time.monotonic()
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or settings.max_output_tokens
            }
        }
        try:
            async with self._client() as c:
                r = await c.post(f"{self.base}/api/chat", json=payload)
        except httpx.TimeoutException as e:
            raise UpstreamTimeout(f"Ollama local inference timed out after {settings.request_timeout:.0f}s", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Cannot reach Ollama at {self.base}: {type(e).__name__}", self.id) from e

        if r.status_code == 404:
            raise ModelUnavailable(f"Local model '{model}' not found in Ollama. Pull it first via 'ollama pull {model}'.", self.id, 404)
        _raise_for_status(self.id, r)

        data = r.json()
        text = (data.get("message") or {}).get("content", "").strip()
        if not text:
            raise EmptyResponse("Local model returned no text", self.id)

        prompt_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)
        return GenResult(text, self.id, data.get("model") or model, time.monotonic() - t0, [],
                         {"prompt": prompt_tokens, "output": output_tokens})

    async def stream(self, messages: List[Message], model: str, *, temperature: float = 0.6,
                     max_tokens: Optional[int] = None) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or settings.max_output_tokens
            }
        }
        got_any = False
        try:
            async with self._client() as c:
                async with c.stream("POST", f"{self.base}/api/chat", json=payload) as r:
                    if r.status_code == 404:
                        raise ModelUnavailable(f"Local model '{model}' not found in Ollama.", self.id, 404)
                    if r.status_code >= 400:
                        await r.aread()
                        _raise_for_status(self.id, r)
                    async for line in r.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            d = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        delta = (d.get("message") or {}).get("content", "")
                        if delta:
                            got_any = True
                            yield delta
        except httpx.TimeoutException as e:
            raise UpstreamTimeout("Local stream timed out", self.id) from e
        except httpx.HTTPError as e:
            raise NetworkError(f"Ollama local connection error: {type(e).__name__}", self.id) from e

        if not got_any:
            raise EmptyResponse("Local stream ended without text", self.id)

    async def list_models(self) -> List[str]:
        try:
            async with self._client() as c:
                r = await c.get(f"{self.base}/api/tags")
            _raise_for_status(self.id, r)
        except httpx.HTTPError as e:
            raise NetworkError(f"Ollama connection error: {type(e).__name__}", self.id) from e
        return [m.get("name", "") for m in r.json().get("models", [])]


def build_registry() -> Dict[str, BaseProvider]:
    reg: Dict[str, BaseProvider] = {"gemini": GeminiProvider(), "ollama": OllamaProvider()}
    for pid in ("openai", "openrouter", "groq", "deepseek"):
        reg[pid] = OpenAICompatProvider(pid)
    return reg
