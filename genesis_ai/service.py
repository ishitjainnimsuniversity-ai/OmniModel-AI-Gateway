"""Chat orchestration: request isolation, context, retries, configured-only fallback, streaming."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from .conversations import Conversation, ConversationStore
from .errors import AuthError, NotConfigured, ProviderError, RateLimited
from .providers import GenResult, Message, build_registry
from .settings import settings

log = logging.getLogger("genesis.service")
MAX_INPUT_CHARS = 4000
MAX_CONCURRENT = 4

# Request lifecycle states reported to clients (and shown on the TFT).
S_QUEUED, S_THINKING, S_SEARCHING, S_TOOL, S_RECEIVING, S_ANSWERING, S_DONE, S_ERROR = (
    "QUEUED", "THINKING", "SEARCHING", "EXECUTING TOOL", "RECEIVING", "ANSWERING", "DONE", "ERROR")


class ChatError(Exception):
    def __init__(self, code: str, message: str, attempts: Optional[list] = None, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.attempts, self.status = code, message, attempts or [], status

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "attempts": self.attempts}


@dataclass
class RequestRecord:
    request_id: str
    conversation_id: str
    state: str = S_QUEUED
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    provider: str = ""
    model: str = ""
    error: Optional[dict] = None


def system_prompt(mode: str, is_local: bool = False) -> str:
    now = datetime.now().astimezone()
    base = (
        "You are GENESIS AI, a capable general-purpose assistant: you explain science, maths, "
        "technology and history, write essays, emails and code, debug, translate, summarise and "
        "brainstorm. Answer the user's actual question directly and accurately. "
        "You have NO live internet access in this conversation unless search results are supplied "
        "in the message. For anything that depends on current events, live prices, weather or "
        "other real-time data, say plainly that you cannot verify it rather than guessing. "
        "Never claim to have performed an action (sending, saving, running code) that you did not do. "
        "If you are unsure, say so. "
        f"Current local date and time of the user's system: {now.strftime('%A, %d %B %Y, %H:%M %Z')}."
    )
    if is_local:
        base += (
            " [OFFLINE LOCAL BRAIN ACTIVE: You are running offline on the user's Windows computer via Ollama. "
            "You have no internet connection. Use your internal knowledge to answer, write code, solve math, and assist. "
            "Do NOT claim to have performed live web research or fetch live news/prices.]"
        )
    if mode == "device":
        base += (" Your reply is shown on a small 320x240 screen: use plain text only (no markdown, "
                 "no tables, no emoji). Be concise by default (about 60-120 words) unless the user "
                 "explicitly asks for a long essay, report or full code.")
    else:
        base += " You may use Markdown for formatting."
    return base


class ChatService:
    def __init__(self, store: Optional[ConversationStore] = None) -> None:
        self.store = store or ConversationStore()
        self.registry = build_registry()
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)
        self._requests: Dict[str, RequestRecord] = {}
        self._last_net_check: float = 0.0
        self._last_net_ok: bool = False

    async def check_internet(self) -> bool:
        """Lightweight non-blocking internet reachability probe, cached for 4.0s."""
        now = time.monotonic()
        if now - self._last_net_check < 4.0:
            return self._last_net_ok
        try:
            import httpx
            async with httpx.AsyncClient(timeout=1.2) as c:
                r = await c.get("http://connectivitycheck.gstatic.com/generate_204")
                self._last_net_ok = (r.status_code == 204)
        except Exception:
            self._last_net_ok = False
        self._last_net_check = now
        return self._last_net_ok

    # ---------------------------------------------------------------- bookkeeping
    def _new_request(self, conv: Conversation) -> RequestRecord:
        rec = RequestRecord(uuid.uuid4().hex[:12], conv.id)
        self._requests[rec.request_id] = rec
        if len(self._requests) > 500:  # drop the oldest finished ones
            for rid in sorted(self._requests, key=lambda r: self._requests[r].updated)[:100]:
                self._requests.pop(rid, None)
        return rec

    def _set(self, rec: RequestRecord, state: str, **kw) -> None:
        rec.state, rec.updated = state, time.time()
        for k, v in kw.items():
            setattr(rec, k, v)

    def request_status(self, rid: str) -> Optional[dict]:
        r = self._requests.get(rid)
        return None if not r else {
            "request_id": r.request_id, "conversation_id": r.conversation_id, "state": r.state,
            "provider": r.provider, "model": r.model, "error": r.error,
            "age_s": round(time.time() - r.created, 1)}

    async def candidates(self) -> List[str]:
        """Dual-brain auto selection: Cloud first if online, falling back to local Ollama.
        If offline or preference='local', directly uses local Ollama without waiting for cloud timeout."""
        pref = settings.mode_preference  # 'auto', 'local', 'cloud'
        ollama_ok = self.registry["ollama"].configured

        if pref == "local":
            return ["ollama"] if ollama_ok else []

        net_ok = await self.check_internet()
        cloud_order = [p for p in ([settings.primary_provider] + settings.fallback_providers) if p in self.registry]

        if pref == "cloud":
            return cloud_order if net_ok else []

        # 'auto' mode:
        if net_ok:
            order = list(cloud_order)
            if ollama_ok and "ollama" not in order:
                order.append("ollama")  # fallback to local if cloud fails or quota runs out
            return order
        else:
            # Offline: route directly to local Ollama
            return ["ollama"] if ollama_ok else []

    def provider_status(self) -> List[dict]:
        out = []
        for pid, p in self.registry.items():
            is_primary = (pid == settings.primary_provider)
            is_fallback = (pid in settings.fallback_providers) or (pid == "ollama" and settings.mode_preference == "auto")
            out.append({"id": pid, "configured": p.configured, "model": settings.model_for(pid),
                        "primary": is_primary, "fallback": is_fallback,
                        "is_local": (pid == "ollama")})
        return out

    def _build(self, conv: Conversation, user_text: str, mode: str, is_local: bool = False) -> List[Message]:
        msgs: List[Message] = [{"role": "system", "content": system_prompt(mode, is_local)}]
        msgs.extend(conv.messages[-settings.history_turns * 2:])
        msgs.append({"role": "user", "content": user_text})
        return msgs

    @staticmethod
    def _validate(text: Optional[str]) -> str:
        t = (text or "").strip()
        if not t:
            raise ChatError("empty_message", "Message is empty.", status=400)
        if len(t) > MAX_INPUT_CHARS:
            raise ChatError("message_too_long", f"Message exceeds {MAX_INPUT_CHARS} characters.",
                            status=413)
        return t

    # ------------------------------------------------------------------- generate
    async def _generate_with_fallback(self, conv: Conversation, text: str, mode: str, rec: RequestRecord) -> GenResult:
        attempts: List[dict] = []
        cands = await self.candidates()
        if not cands:
            raise ChatError("no_brain_available",
                            "No AI brain is currently available. Either connect to the internet for Cloud AI, "
                            "or start Ollama locally on Windows for Offline AI.", status=503)

        for pid in cands:
            prov = self.registry[pid]
            if not prov.configured:
                attempts.append(NotConfigured(f"{prov.env_name or pid} not configured/ready", pid).to_dict())
                continue
            is_local = (pid == "ollama")
            msgs = self._build(conv, text, mode, is_local=is_local)
            for model in settings.models_for(pid):
                res, key_rejected = await self._try_model(prov, pid, model, msgs, rec, attempts)
                if res:
                    return res
                if key_rejected:
                    break  # a rejected key fails every model of this provider
        raise ChatError("all_providers_failed", self._explain(attempts), attempts)

    async def _try_model(self, prov, pid: str, model: str, msgs: List[Message],
                         rec: RequestRecord, attempts: List[dict]):
        """Call one model with bounded retries. Returns (result|None, key_rejected)."""
        for attempt in range(settings.max_retries + 1):
            try:
                self._set(rec, S_THINKING, provider=pid, model=model)
                return await prov.generate(msgs, model), False
            except ProviderError as e:
                attempts.append({**e.to_dict(), "attempt": attempt + 1, "model": model})
                log.warning("req=%s provider=%s model=%s attempt=%d -> %s (%s) %s",
                            rec.request_id, pid, model, attempt + 1, e.code, e.status,
                            e.message[:160])
                last_try = attempt >= settings.max_retries
                if isinstance(e, RateLimited) and e.retry_after and e.retry_after <= 3 and not last_try:
                    await asyncio.sleep(e.retry_after)
                    continue
                if e.retryable and not last_try:
                    await asyncio.sleep(0.6 * (attempt + 1))
                    continue
                return None, isinstance(e, AuthError)
        return None, False

    @staticmethod
    def _explain(attempts: List[dict]) -> str:
        if not attempts:
            return "No AI provider is configured."
        last = attempts[-1]
        if last.get("provider") == "ollama":
            if last.get("code") == "not_configured":
                return "Ollama is not reachable locally on Windows. Start Ollama at http://127.0.0.1:11434."
            if last.get("code") in ("network_error", "timeout"):
                return "Cannot reach Ollama at http://127.0.0.1:11434 - service may be stopped."
            if last.get("code") == "model_unavailable":
                return last.get("message") or "Requested local model is not installed in Ollama."
        hints = {
            "auth_failed": "The API key was rejected - check the key in the backend .env.",
            "rate_limited": "The AI provider's rate limit or quota was exceeded - try again later.",
            "model_unavailable": "The selected model is not available - change GENESIS_MODEL.",
            "timeout": "The AI provider did not answer in time.",
            "network_error": "The backend could not reach the AI provider (no internet?).",
            "not_configured": "No API key is set for the selected provider.",
            "empty_response": "The model returned an empty answer.",
        }
        return hints.get(last["code"], f"AI provider error: {last['message']}")

    async def chat(self, message: Optional[str], conversation_id: Optional[str] = None,
                   mode: str = "web") -> dict:
        text = self._validate(message)
        conv = self.store.get_or_create(conversation_id)
        rec = self._new_request(conv)
        try:
            async with self._sem:
                async with conv.lock:  # one in-flight turn per conversation keeps context ordered
                    res = await self._generate_with_fallback(conv, text, mode, rec)
                    self.store.append_turn(conv, text, res.text, settings.history_turns)
        except ChatError as e:
            self._set(rec, S_ERROR, error=e.to_dict())
            e.request_id, e.conversation_id = rec.request_id, conv.id  # type: ignore[attr-defined]
            raise
        self._set(rec, S_DONE, provider=res.provider, model=res.model)
        brain = "LOCAL" if res.provider == "ollama" else "CLOUD"
        mode_str = "OFFLINE" if brain == "LOCAL" else "ONLINE"
        fallback_flag = (res.provider == "ollama" and settings.mode_preference != "local" and settings.primary_provider != "ollama")

        return {"request_id": rec.request_id, "conversation_id": conv.id, "text": res.text,
                "provider": res.provider, "model": res.model, "brain": brain, "mode": mode_str,
                "fallback": fallback_flag, "latency_s": round(res.latency_s, 2),
                "sources": res.sources, "usage": res.usage,
                "retrieved_at": datetime.now().astimezone().isoformat(timespec="seconds")}

    # ------------------------------------------------------------------ streaming
    async def chat_stream(self, message: Optional[str], conversation_id: Optional[str] = None,
                          mode: str = "web") -> AsyncIterator[dict]:
        try:
            text = self._validate(message)
        except ChatError as e:
            yield {"type": "error", **e.to_dict()}
            return
        conv = self.store.get_or_create(conversation_id)
        rec = self._new_request(conv)
        yield {"type": "start", "request_id": rec.request_id, "conversation_id": conv.id,
               "state": S_THINKING}
        attempts: List[dict] = []
        cands = await self.candidates()
        if not cands:
            err = ChatError("no_brain_available", "No AI brain is available. Start Ollama locally or connect to internet for Cloud AI.", status=503)
            self._set(rec, S_ERROR, error=err.to_dict())
            yield {"type": "error", **err.to_dict(), "request_id": rec.request_id}
            return

        async with self._sem:
            async with conv.lock:
                pairs = []
                for pid in cands:
                    prov = self.registry[pid]
                    if not prov.configured:
                        attempts.append(NotConfigured(f"{prov.env_name or pid} not configured", pid).to_dict())
                        continue
                    pairs += [(pid, m) for m in settings.models_for(pid)]
                rejected: set = set()
                for pid, model in pairs:
                    if pid in rejected:
                        continue
                    prov = self.registry[pid]
                    is_local = (pid == "ollama")
                    brain = "LOCAL" if is_local else "CLOUD"
                    mode_str = "OFFLINE" if is_local else "ONLINE"
                    fallback_flag = (is_local and settings.mode_preference != "local" and settings.primary_provider != "ollama")
                    msgs = self._build(conv, text, mode, is_local=is_local)

                    self._set(rec, S_THINKING, provider=pid, model=model)
                    parts: List[str] = []
                    try:
                        async for delta in prov.stream(msgs, model):
                            if not parts:
                                self._set(rec, S_ANSWERING)
                                yield {"type": "meta", "provider": pid, "model": model,
                                       "brain": brain, "mode": mode_str, "fallback": fallback_flag,
                                       "state": S_ANSWERING}
                            parts.append(delta)
                            yield {"type": "delta", "text": delta}
                    except ProviderError as e:
                        attempts.append({**e.to_dict(), "model": model})
                        log.warning("req=%s stream provider=%s model=%s -> %s (%s) %s", rec.request_id,
                                    pid, model, e.code, e.status, e.message[:160])
                        if parts:  # already partially streamed: cannot silently switch provider
                            self._set(rec, S_ERROR, error=e.to_dict())
                            yield {"type": "error", "code": e.code,
                                   "message": "Stream interrupted: " + e.message,
                                   "partial": True, "request_id": rec.request_id}
                            return
                        if isinstance(e, AuthError):
                            rejected.add(pid)
                        continue
                    full = "".join(parts).strip()
                    self.store.append_turn(conv, text, full, settings.history_turns)
                    self._set(rec, S_DONE)
                    yield {"type": "done", "request_id": rec.request_id,
                           "conversation_id": conv.id, "provider": pid, "model": model,
                           "brain": brain, "mode": mode_str, "fallback": fallback_flag,
                           "text": full}
                    return
        err = ChatError("all_providers_failed", self._explain(attempts), attempts)
        self._set(rec, S_ERROR, error=err.to_dict())
        yield {"type": "error", **err.to_dict(), "request_id": rec.request_id}
