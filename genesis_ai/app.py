"""GENESIS AI backend API (FastAPI). Run:  python -m genesis_ai
Secrets never leave the backend. All /api routes except /api/health need the LAN access token."""
from __future__ import annotations

import json
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import __version__
from .errors import ProviderError
from .feed import feed
from .formatting import device_text, paginate
from .service import ChatError, ChatService
from .settings import settings
from .system_info import SystemInspector

WEB_DIR = Path(__file__).resolve().parent / "web"
service = ChatService()
app = FastAPI(title="GENESIS AI Backend", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------------------ auth
def require_token(request: Request, x_genesis_token: Optional[str] = Header(None),
                  authorization: Optional[str] = Header(None),
                  token: Optional[str] = Query(None)) -> None:
    supplied = x_genesis_token or token or ""
    if not supplied and authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if not secrets.compare_digest(supplied.encode(), settings.access_token().encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing access token")


# ---------------------------------------------------------------------------- schemas
class ChatBody(BaseModel):
    message: Optional[str] = None
    conversation_id: Optional[str] = None


class DeviceChatBody(ChatBody):
    cols: int = Field(26, ge=10, le=80)
    rows: int = Field(8, ge=1, le=40)


def _chat_error_response(e: ChatError) -> JSONResponse:
    status = e.status
    if e.code == "all_providers_failed" and e.attempts and e.attempts[-1].get("code") == "rate_limited":
        status = 429
    body = {"error": e.to_dict(), "request_id": getattr(e, "request_id", None),
            "conversation_id": getattr(e, "conversation_id", None)}
    return JSONResponse(body, status_code=status)


# --------------------------------------------------------------------------- health
_deep_cache: Dict[str, object] = {"t": 0.0, "ok": False, "detail": ""}


@app.get("/api/health")
async def health(deep: bool = False):
    provs = service.provider_status()
    primary = next((p for p in provs if p["primary"]), None)
    ollama_prov = service.registry.get("ollama")
    local_ai_ok = bool(ollama_prov and ollama_prov.configured)
    cloud_ai_ok = bool(primary and primary["configured"] and not primary.get("is_local"))
    net_ok = await service.check_internet()

    # Determine which brain is active right now
    if settings.mode_preference == "local":
        active_brain = "LOCAL" if local_ai_ok else "NONE"
    elif settings.mode_preference == "cloud":
        active_brain = "CLOUD" if (net_ok and cloud_ai_ok) else "NONE"
    else:  # 'auto'
        if net_ok and cloud_ai_ok:
            active_brain = "CLOUD"
        elif local_ai_ok:
            active_brain = "LOCAL"
        else:
            active_brain = "NONE"

    active_mode = "ONLINE" if active_brain == "CLOUD" else "OFFLINE"

    out = {
        "status": "ok",
        "version": __version__,
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "primary": primary,
        "providers": provs,
        "ai_ready": local_ai_ok or cloud_ai_ok,
        "local_ai_available": local_ai_ok,
        "local_model": settings.local_model,
        "cloud_ai_available": cloud_ai_ok,
        "cloud_model": primary["model"] if primary else "",
        "internet_accessible": net_ok,
        "mode_preference": settings.mode_preference,
        "active_brain": active_brain,
        "active_mode": active_mode
    }
    if deep and cloud_ai_ok and net_ok:
        if time.time() - float(_deep_cache["t"]) > 120:
            try:  # cheap authenticated call proves key + internet without spending tokens
                models = await service.registry[settings.primary_provider].list_models()
                _deep_cache.update(t=time.time(), ok=True, detail=f"{len(models)} models")
            except ProviderError as e:
                _deep_cache.update(t=time.time(), ok=False, detail=e.code)
        out["cloud_reachable"] = _deep_cache["ok"]
        out["cloud_detail"] = _deep_cache["detail"]
    elif not net_ok:
        out["cloud_reachable"] = False
        out["cloud_detail"] = "no internet connection (offline)"
    return out


# ----------------------------------------------------------- System & Model Management
@app.get("/api/system/specs", dependencies=[Depends(require_token)])
async def system_specs():
    """Inspects Windows RAM, CPU, GPU, free disk and returns recommended model."""
    return await SystemInspector.get_recommendations()


@app.get("/api/ollama/models", dependencies=[Depends(require_token)])
async def ollama_models():
    """Returns list of installed local Ollama models and the active model."""
    models = await SystemInspector.get_ollama_models()
    return {
        "installed_models": models,
        "active_model": settings.local_model,
        "base_url": settings.ollama_base_url
    }


@app.post("/api/ollama/switch", dependencies=[Depends(require_token)])
async def switch_ollama_model(model: str = Query(...)):
    """Switches the active local model in Ollama."""
    settings.set_local_model(model)
    return {"ok": True, "active_local_model": settings.local_model}


@app.post("/api/system/mode", dependencies=[Depends(require_token)])
async def set_system_mode(mode: str = Query(..., pattern="^(auto|cloud|local)$")):
    """Sets dual-brain mode: 'auto' (preferred), 'cloud', or 'local' (offline)."""
    ok = settings.set_mode_preference(mode)
    return {"ok": ok, "mode": settings.mode_preference}


# ----------------------------------------------------------------------------- chat
@app.post("/api/chat", dependencies=[Depends(require_token)])
async def chat(body: ChatBody):
    tracked = bool((body.message or "").strip())
    if tracked:
        feed.begin(body.message, body.conversation_id, "phone")
    try:
        res = await service.chat(body.message, body.conversation_id, mode="web")
    except ChatError as e:
        if tracked:
            feed.fail(e.message, getattr(e, "request_id", "") or "")
        return _chat_error_response(e)
    feed.finish(res)
    return res


@app.post("/api/chat/stream", dependencies=[Depends(require_token)])
async def chat_stream(body: ChatBody):
    tracked = bool((body.message or "").strip())
    if tracked:
        feed.begin(body.message, body.conversation_id, "phone")

    async def gen():
        async for ev in service.chat_stream(body.message, body.conversation_id, mode="web"):
            if tracked and ev["type"] == "done":
                feed.finish(ev)
            elif tracked and ev["type"] == "error":
                feed.fail(ev.get("message", "error"), ev.get("request_id", ""))
            yield f"data: {json.dumps(ev)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/requests/{rid}", dependencies=[Depends(require_token)])
async def request_status(rid: str):
    st = service.request_status(rid)
    if not st:
        raise HTTPException(404, "Unknown request id")
    return st


# ---------------------------------------------------------------------- conversations
@app.post("/api/conversations", dependencies=[Depends(require_token)])
async def new_conversation():
    conv = service.store.create()
    feed.reset()
    return conv.public()


@app.get("/api/conversations", dependencies=[Depends(require_token)])
async def list_conversations():
    return {"conversations": service.store.list()}


@app.get("/api/conversations/{cid}", dependencies=[Depends(require_token)])
async def get_conversation(cid: str):
    c = service.store.get(cid)
    if not c:
        raise HTTPException(404, "Unknown conversation")
    return c.public()


@app.post("/api/conversations/{cid}/clear", dependencies=[Depends(require_token)])
async def clear_conversation(cid: str):
    if not service.store.clear(cid):
        raise HTTPException(404, "Unknown conversation")
    if feed.conversation_id == cid:
        feed.reset()
    return {"ok": True, "conversation_id": cid}


@app.delete("/api/conversations/{cid}", dependencies=[Depends(require_token)])
async def delete_conversation(cid: str):
    if not service.store.delete(cid):
        raise HTTPException(404, "Unknown conversation")
    return {"ok": True}


# ------------------------------------------------------------------------- device API
_device_results: Dict[str, dict] = {}


def _prune_device() -> None:
    cutoff = time.time() - 1800
    for rid in [r for r, v in _device_results.items() if v["t"] < cutoff]:
        _device_results.pop(rid, None)


@app.get("/api/device/feed", dependencies=[Depends(require_token)])
async def device_feed(seq: int = 0, cols: int = Query(26, ge=10, le=80),
                      rows: int = Query(9, ge=1, le=40)):
    """Polled by the ESP32. Returns a tiny status unless something changed since `seq`."""
    return feed.view(seq, cols, rows)


@app.get("/api/device/feed/page", dependencies=[Depends(require_token)])
async def device_feed_page(page: int = 0, cols: int = Query(26, ge=10, le=80),
                           rows: int = Query(9, ge=1, le=40)):
    return feed.page(cols, rows, page)


@app.post("/api/device/new", dependencies=[Depends(require_token)])
async def device_new_conversation():
    """BOOT-button long press on the device: start a fresh conversation."""
    conv = service.store.create()
    feed.reset()
    return {"conversation_id": conv.id}


@app.post("/api/device/chat", dependencies=[Depends(require_token)])
async def device_chat(body: DeviceChatBody):
    tracked = bool((body.message or "").strip())
    if tracked:
        feed.begin(body.message, body.conversation_id, "device")
    try:
        res = await service.chat(body.message, body.conversation_id, mode="device")
    except ChatError as e:
        if tracked:
            feed.fail(e.message, getattr(e, "request_id", "") or "")
        return _chat_error_response(e)
    feed.finish(res)
    txt = device_text(res["text"])
    pages = paginate(txt, body.cols, body.rows)
    _prune_device()
    _device_results[res["request_id"]] = {"t": time.time(), "text": txt}
    return {"request_id": res["request_id"], "conversation_id": res["conversation_id"],
            "provider": res["provider"], "model": res["model"], "latency_s": res["latency_s"],
            "page": 0, "total_pages": len(pages), "text": pages[0], "chars": len(txt)}


@app.get("/api/device/page", dependencies=[Depends(require_token)])
async def device_page(request_id: str, page: int = 0, cols: int = 26, rows: int = 8):
    rec = _device_results.get(request_id)
    if not rec:
        raise HTTPException(404, "Result expired or unknown")
    pages = paginate(rec["text"], cols, rows)
    page = max(0, min(page, len(pages) - 1))
    return {"request_id": request_id, "page": page, "total_pages": len(pages), "text": pages[page]}


# ---------------------------------------------------------------------------- web UI
@app.get("/")
async def index():
    f = WEB_DIR / "index.html"
    if f.exists():
        return FileResponse(f)
    return JSONResponse({"service": "GENESIS AI Backend", "version": __version__,
                         "docs": "/docs", "health": "/api/health"})


def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    tok = settings.access_token()
    print("=" * 62)
    print(f" GENESIS AI backend v{__version__}  on port {settings.port}")
    print(f" Primary provider : {settings.primary_provider} / {settings.model_for(settings.primary_provider)}")
    print(f" Fallbacks        : {settings.fallback_providers or 'none configured'}")
    print(f" Access token     : {tok}")
    print("=" * 62)
    uvicorn.run(app, host="0.0.0.0", port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
