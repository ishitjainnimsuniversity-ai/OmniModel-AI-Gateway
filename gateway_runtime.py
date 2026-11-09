"""
OmniModel AI Universal Gateway Server
Serves OpenAI-compatible proxy, multi-model arena, smart routing, and web dashboard.
"""

import asyncio
import json
import mimetypes
import os
import re
import shutil
import socket
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_CORE_IMPORT_ERROR: Optional[str] = None
try:
    from core.config import GatewayConfig
    from core.providers import PROVIDERS_METADATA
    from core.adapters import UniversalAdapter
    from core.router import SmartRouter
    from core.analytics import AnalyticsTracker
    from core.screen_bridge import hardware_bridge
except Exception:
    _CORE_IMPORT_ERROR = traceback.format_exc()
    print(f"[server.py] Core import error:\n{_CORE_IMPORT_ERROR}", file=sys.stderr)
    PROVIDERS_METADATA = {}

    class GatewayConfig:  # type: ignore
        PORT = int(((os.getenv("PORT") or "").strip()) or "8000") if ((os.getenv("PORT") or "").strip().isdigit()) else 8000
        HOST = (os.getenv("HOST") or "").strip() or "0.0.0.0"

        @classmethod
        def get_key(cls, k: str):
            return os.getenv(k)

        @classmethod
        def set_key(cls, k: str, v: str):
            return False

        @classmethod
        def get_active_providers_status(cls, d):
            return {}

    UniversalAdapter = None  # type: ignore
    SmartRouter = None  # type: ignore
    AnalyticsTracker = None  # type: ignore
    hardware_bridge = None  # type: ignore

try:
    import psutil
except ImportError:
    psutil = None


def _is_cloud_env() -> bool:
    return bool(
        os.getenv("VERCEL")
        or os.getenv("VERCEL_ENV")
        or os.getenv("VERCEL_URL")
        or os.getenv("VERCEL_REGION")
        or os.getenv("VERCEL_DEPLOYMENT_ID")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        or os.getenv("AWS_EXECUTION_ENV")
        or os.getenv("LAMBDA_TASK_ROOT")
        or os.getenv("RENDER")
        or os.getenv("DYNO")
        or os.getenv("RAILWAY_ENVIRONMENT")
    )


def _is_loopback_request(request: Request) -> bool:
    """Returns True only for direct local loopback access (not proxied via Cloudflare/Vercel/public)."""
    if _is_cloud_env():
        return False
    proxy_headers = ("cf-connecting-ip", "x-vercel-id", "x-forwarded-for", "x-forwarded-host", "true-client-ip")
    if any(request.headers.get(h) for h in proxy_headers):
        return False
    client_host = request.client.host if request.client else ""
    return client_host in ("127.0.0.1", "::1", "localhost")


app = FastAPI(
    title="OmniModel Universal AI Gateway",
    description="2026 Master Multi-Model Hub & Router for Antigravity",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not _is_cloud_env():
    @app.on_event("startup")
    async def _startup_hardware_bridge():
        if hardware_bridge is not None:
            hardware_bridge.start_background_tasks()


PUBLIC_DIR = BASE_DIR / "public"


@app.get("/static/{file_path:path}")
async def serve_static_asset(file_path: str):
    from fastapi.responses import FileResponse

    base = PUBLIC_DIR.resolve()
    target = (base / file_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    media_type, _ = mimetypes.guess_type(str(target))
    return FileResponse(str(target), media_type=media_type or "application/octet-stream")


@app.get("/style.css")
async def get_style_css():
    css_path = PUBLIC_DIR / "style.css"
    if css_path.exists():
        return Response(content=css_path.read_text(encoding="utf-8"), media_type="text/css")
    return Response(content="", media_type="text/css")


@app.get("/app.js")
async def get_app_js():
    js_path = PUBLIC_DIR / "app.js"
    if js_path.exists():
        return Response(content=js_path.read_text(encoding="utf-8"), media_type="application/javascript")
    return Response(content="", media_type="application/javascript")


@app.get("/assistant_logo.png")
@app.get("/assistant_logo")
@app.get("/logo.png")
@app.get("/logo")
@app.get("/quantum_engine.png")
@app.get("/quantum_engine_logo.jpg")
@app.get("/assistant_avatar.jpg")
async def get_assistant_logo():
    from fastapi.responses import FileResponse
    for name in ["assistant_logo.png", "quantum_engine_logo.jpg", "assistant_avatar.jpg", "quantum_engine.png", "logo.png"]:
        p = PUBLIC_DIR / name
        if p.exists():
            media = "image/png" if name.endswith(".png") else "image/jpeg"
            return FileResponse(str(p), media_type=media)
    return JSONResponse(status_code=404, content={"error": "Logo not found"})


@app.get("/favicon.ico")
async def get_favicon():
    from fastapi.responses import FileResponse
    p = PUBLIC_DIR / "assistant_logo.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    return Response(status_code=204)


@app.get("/ai_wheel.png")
async def get_ai_wheel_png():
    from fastapi.responses import FileResponse
    p = PUBLIC_DIR / "ai_wheel.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "ai_wheel not found"})


@app.get("/quantum_core.png")
async def get_quantum_core_png():
    from fastapi.responses import FileResponse
    p = PUBLIC_DIR / "quantum_core.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "quantum_core not found"})


@app.get("/quantum_fusion_core.png")
async def get_quantum_fusion_core_png():
    from fastapi.responses import FileResponse
    p = PUBLIC_DIR / "quantum_fusion_core.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "fusion core not found"})


@app.get("/Quantum Core in a Neon Lab.png")
async def get_quantum_core_orig_png():
    from fastapi.responses import FileResponse
    p = PUBLIC_DIR / "quantum_core.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "image not found"})


# Request Models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class KeyUpdateRequest(BaseModel):
    env_var: Optional[str] = None
    env_key: Optional[str] = None
    value: Optional[str] = None
    api_key: Optional[str] = None


class ArenaRequest(BaseModel):
    models: List[Dict[str, str]]  # [{"provider": "groq", "model": "llama-3.3-70b-versatile"}, ...]
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


# -----------------------------------------------------------------------------
# 1. Web Dashboard & 2.4" Hardware Screen Delivery
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = PUBLIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>OmniModel Gateway UI Loading...</h1>"


@app.get("/screen", response_class=HTMLResponse)
@app.get("/screen/", response_class=HTMLResponse)
@app.get("/screen_preview.html", response_class=HTMLResponse)
@app.get("/screen_preview", response_class=HTMLResponse)
@app.get("/preview", response_class=HTMLResponse)
@app.get("/preview/", response_class=HTMLResponse)
@app.get("/display", response_class=HTMLResponse)
@app.get("/display/", response_class=HTMLResponse)
@app.get("/hardware", response_class=HTMLResponse)
@app.get("/hardware/", response_class=HTMLResponse)
@app.get("/iot", response_class=HTMLResponse)
@app.get("/iot/", response_class=HTMLResponse)
@app.get("/simulator", response_class=HTMLResponse)
@app.get("/simulator/", response_class=HTMLResponse)
@app.get("/lcd", response_class=HTMLResponse)
@app.get("/lcd/", response_class=HTMLResponse)
async def serve_screen_preview():
    screen_file = PUBLIC_DIR / "screen_preview.html"
    if screen_file.exists():
        return screen_file.read_text(encoding="utf-8")
    return "<h1>2.4\" Screen Preview Loading...</h1>"


@app.get("/ip")
async def get_server_ip(request: Request):
    hostname = socket.gethostname()
    all_ips = []
    wifi_ip = None
    port = GatewayConfig.PORT

    if _is_cloud_env():
        host_hdr = request.headers.get("x-forwarded-host") or request.headers.get("host") or "omni-model-ai-gateway.vercel.app"
        proto = request.headers.get("x-forwarded-proto") or "https"
        base_url = f"{proto}://{host_hdr}"
        return {
            "status": "online",
            "mode": "cloud",
            "hostname": hostname,
            "wifi_ip": host_hdr,
            "recommended_screen_url": f"{base_url}/screen",
            "recommended_dashboard_url": f"{base_url}/",
            "localhost_screen_url": f"http://localhost:{port}/screen",
            "iot_endpoint": f"{base_url}/api/iot/chat",
            "all_interfaces": [],
            "port": port
        }

    if psutil is not None:
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127.") and not addr.address.startswith("169.254."):
                        is_wifi = any(w in iface.lower() for w in ["wi-fi", "wireless", "wlan"])
                        all_ips.append({"interface": iface, "ip": addr.address, "is_wifi": is_wifi})
                        if is_wifi and not wifi_ip:
                            wifi_ip = addr.address
        except Exception:
            pass

    if not wifi_ip:
        try:
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    all_ips.append({"interface": "host", "ip": ip, "is_wifi": True})
                    wifi_ip = ip
                    break
        except Exception:
            pass

    if not wifi_ip and all_ips:
        wifi_ip = all_ips[0]["ip"]
    if not wifi_ip:
        wifi_ip = "127.0.0.1"

    return {
        "status": "online",
        "hostname": hostname,
        "wifi_ip": wifi_ip,
        "recommended_screen_url": f"http://{wifi_ip}:{port}/screen",
        "recommended_dashboard_url": f"http://{wifi_ip}:{port}/",
        "localhost_screen_url": f"http://localhost:{port}/screen",
        "iot_endpoint": f"http://{wifi_ip}:{port}/api/iot/chat",
        "all_interfaces": all_ips,
        "port": port
    }


# -----------------------------------------------------------------------------
# 2. OpenAI-Compatible Gateway Endpoints (/v1/models & /v1/chat/completions)
# -----------------------------------------------------------------------------
@app.get("/v1/models")
async def list_openai_models():
    model_list = []
    # GENESIS AI 5.0 Flagship Models
    model_list.append({"id": "genesis-ai-5.0", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 (Frontier Cognitive Auto-Router)"})
    model_list.append({"id": "genesis-5.0-reasoning", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 Deep Reasoning (DeepSeek R1 / o3 / Gemini Thinking)"})
    model_list.append({"id": "genesis-5.0-speed", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 Ultra-Speed (<100ms Groq / Cerebras)"})
    model_list.append({"id": "genesis-5.0-coder", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 Elite Coder (Claude 3.7 / Codestral / Gemini Pro)"})
    model_list.append({"id": "genesis-5.0-free", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 100% Free Tier (Zero-Cost Models)"})
    model_list.append({"id": "genesis-5.0-search", "object": "model", "owned_by": "genesis-ai", "name": "GENESIS AI 5.0 Live Web Search (Perplexity / Grounded)"})
    model_list.append({"id": "genesis-5.0", "object": "model", "owned_by": "genesis-ai"})
    model_list.append({"id": "auto", "object": "model", "owned_by": "genesis-ai"})
    model_list.append({"id": "free_tier", "object": "model", "owned_by": "genesis-ai"})

    for pid, meta in PROVIDERS_METADATA.items():
        for m in meta.get("models", []):
            model_list.append({
                "id": f"{pid}/{m['id']}",
                "object": "model",
                "owned_by": pid,
                "name": m["name"],
                "context": m.get("context", "128k"),
                "speed": m.get("speed", "Fast"),
                "free_tier": m.get("free", False)
            })
    return {"object": "list", "data": model_list}


@app.post("/v1/chat/completions")
async def openai_chat_completions(req: ChatCompletionRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "OpenAI-Client")
    req_model = req.model.strip()
    raw_messages = [{"role": m.role, "content": m.content} for m in req.messages]
    prompt_snippet = raw_messages[-1]["content"] if raw_messages else ""

    # Check if this is a virtual router model (genesis-ai-5.0, auto, free_tier, reasoning, speed, coding, search)
    genesis_profiles = {
        "genesis-ai-5.0": None,
        "genesis-5.0": None,
        "genesis-5.0-reasoning": "reasoning",
        "genesis-5.0-speed": "speed",
        "genesis-5.0-coder": "coding",
        "genesis-5.0-free": "free_tier",
        "genesis-5.0-search": "search",
        "alfa-ai-5.0": None,
        "alfa-5.0": None,
        "auto": None,
        "free_tier": "free_tier",
        "reasoning": "reasoning",
        "speed": "speed",
        "coding": "coding",
        "search": "search"
    }

    if req_model in genesis_profiles or req_model.startswith("profile:"):
        profile = genesis_profiles.get(req_model) if req_model in genesis_profiles else req_model.replace("profile:", "")

        if req.stream:
            async def event_generator():
                created = int(time.time())
                async for chunk in SmartRouter.route_and_execute_stream(
                    messages=raw_messages,
                    profile_override=profile,
                    temperature=req.temperature or 0.7,
                    max_tokens=req.max_tokens or 2048
                ):
                    delta = chunk.get("delta", "")
                    if delta:
                        data = {
                            "id": f"chatcmpl-{int(time.time()*1000)}",
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": req_model,
                            "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}]
                        }
                        yield f"data: {json.dumps(data)}\n\n"

                # End of stream
                end_data = {
                    "id": f"chatcmpl-{int(time.time()*1000)}",
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req_model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
                yield f"data: {json.dumps(end_data)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")
        else:
            full_text = []
            async for chunk in SmartRouter.route_and_execute_stream(
                messages=raw_messages,
                profile_override=profile,
                temperature=req.temperature or 0.7,
                max_tokens=req.max_tokens or 2048
            ):
                delta = chunk.get("delta", "")
                if delta:
                    full_text.append(delta)

            content = "".join(full_text)
            return {
                "id": f"chatcmpl-{int(time.time()*1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req_model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop"
                }]
            }

    # Direct model specified (format: "provider/model" or model name)
    if "/" in req_model:
        provider_id, target_model = req_model.split("/", 1)
    else:
        # Infer provider from model name
        provider_id = None
        target_model = req_model
        for pid, meta in PROVIDERS_METADATA.items():
            for m in meta.get("models", []):
                if m["id"] == req_model or req_model.startswith(m["id"]):
                    provider_id = pid
                    break
            if provider_id:
                break
        if not provider_id:
            provider_id = "openrouter"

    if req.stream:
        async def direct_event_generator():
            created = int(time.time())
            async for chunk in UniversalAdapter.chat_stream(
                provider_id=provider_id,
                model=target_model,
                messages=raw_messages,
                temperature=req.temperature or 0.7,
                max_tokens=req.max_tokens or 2048
            ):
                delta = chunk.get("delta", "")
                if delta:
                    data = {
                        "id": f"chatcmpl-{int(time.time()*1000)}",
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": req_model,
                        "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(data)}\n\n"

            end_data = {
                "id": f"chatcmpl-{int(time.time()*1000)}",
                "object": "chat.completion.chunk",
                "created": created,
                "model": req_model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(end_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(direct_event_generator(), media_type="text/event-stream")
    else:
        full_text = []
        async for chunk in UniversalAdapter.chat_stream(
            provider_id=provider_id,
            model=target_model,
            messages=raw_messages,
            temperature=req.temperature or 0.7,
            max_tokens=req.max_tokens or 2048
        ):
            delta = chunk.get("delta", "")
            if delta:
                full_text.append(delta)

        content = "".join(full_text)
        return {
            "id": f"chatcmpl-{int(time.time()*1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req_model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }]
        }


# -----------------------------------------------------------------------------
# 3. Provider Management & Live Health Checks
# -----------------------------------------------------------------------------
@app.get("/api/providers")
@app.get("/providers")
async def get_providers():
    status = GatewayConfig.get_active_providers_status(PROVIDERS_METADATA)
    return {"success": True, "providers": status, "total": len(status)}


@app.get("/api/analytics")
@app.get("/analytics")
async def get_user_analytics():
    """Returns analytics of users and requests who have used the app"""
    summary = AnalyticsTracker.get_summary()
    return {"success": True, "analytics": summary}


@app.post("/api/analytics/clear")
@app.post("/analytics/clear")
async def clear_user_analytics():
    AnalyticsTracker.clear_records()
    return {"success": True, "message": "Analytics history cleared"}


@app.get("/api/keys")
@app.get("/keys")
async def get_api_keys(request: Request):
    configured = {
        "GEMINI_API_KEY": bool(GatewayConfig.get_key("GEMINI_API_KEY")),
        "OPENROUTER_API_KEY": bool(GatewayConfig.get_key("OPENROUTER_API_KEY")),
        "GROQ_API_KEY": bool(GatewayConfig.get_key("GROQ_API_KEY")),
    }
    if not _is_loopback_request(request):
        return {
            "GEMINI_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            "GROQ_API_KEY": "",
            "configured": configured,
            "masked": True,
        }
    return {
        "GEMINI_API_KEY": GatewayConfig.get_key("GEMINI_API_KEY") or "",
        "OPENROUTER_API_KEY": GatewayConfig.get_key("OPENROUTER_API_KEY") or "",
        "GROQ_API_KEY": GatewayConfig.get_key("GROQ_API_KEY") or "",
        "configured": configured,
        "masked": False,
    }


@app.post("/api/keys")
@app.post("/keys")
async def update_api_key(req: KeyUpdateRequest, request: Request):
    if not _is_loopback_request(request):
        raise HTTPException(
            status_code=403,
            detail="Remote/cloud environments do not allow overwriting server .env keys over HTTP; configure environment variables directly."
        )
    target_var = (req.env_var or req.env_key or "").strip()
    target_val = (req.value or req.api_key or "").strip()
    if not target_var:
        raise HTTPException(status_code=400, detail="Missing environment variable name")
    success = GatewayConfig.set_key(target_var, target_val)
    if success:
        return {"success": True, "message": f"Successfully updated {target_var}"}
    raise HTTPException(status_code=500, detail="Failed to write key to .env")


@app.post("/api/ping/{provider_id}")
@app.post("/ping/{provider_id}")
async def ping_provider(provider_id: str):
    result = await UniversalAdapter.test_ping(provider_id)
    return result


@app.get("/api/health")
@app.get("/health")
async def health_check():
    if _CORE_IMPORT_ERROR is not None:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "service": "OmniModel AI Gateway",
                "version": "2.0.0",
                "cloud_mode": _is_cloud_env(),
                "core_loaded": False,
                "core_error": _CORE_IMPORT_ERROR,
            },
        )
    return {
        "status": "ok",
        "service": "OmniModel AI Gateway",
        "version": "2.0.0",
        "cloud_mode": _is_cloud_env(),
        "core_loaded": True,
    }


# -----------------------------------------------------------------------------
# 4. Interactive Dashboard SSE Streaming Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/chat/stream")
@app.post("/chat/stream")
async def api_chat_stream(
    request: Request,
    messages: Optional[List[Dict[str, Any]]] = Body(None),
    prompt: Optional[str] = Body(None),
    provider: Optional[str] = Body(None),
    model: Optional[str] = Body(None),
    profile: Optional[str] = Body(None),
    temperature: float = Body(0.7),
    max_tokens: int = Body(2048)
):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "Web-Browser")

    if messages:
        raw_messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]
    elif prompt:
        raw_messages = [{"role": "user", "content": prompt}]
    else:
        raw_messages = [{"role": "user", "content": "Hello"}]

    prompt_snippet = raw_messages[-1]["content"] if raw_messages else ""
    api_key_override = request.headers.get("x-gemini-api-key") or request.headers.get("x-api-key") or None
    start_time = time.perf_counter()

    async def sse_generator():
        total_text = []
        actual_provider = provider or ("Gemini" if SmartRouter.check_internet() else "Ollama")
        actual_model = model or ("gemini-3.5-flash-lite" if SmartRouter.check_internet() else "llama3.2:1b")

        # Signal thinking state to physical 2.4-inch screen
        try:
            hardware_bridge.send_thinking(prompt_snippet, actual_provider, actual_model)
        except Exception:
            pass

        if provider and provider != "auto":
            target_model = model or PROVIDERS_METADATA.get(provider, {}).get("default_model", "")
            async for chunk in UniversalAdapter.chat_stream(
                provider_id=provider,
                model=target_model,
                messages=raw_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key_override=api_key_override
            ):
                if chunk.get("delta"):
                    total_text.append(chunk["delta"])
                chunk["content"] = chunk.get("delta", "")
                yield f"data: {json.dumps(chunk)}\n\n"
        else:
            async for chunk in SmartRouter.route_and_execute_stream(
                messages=raw_messages,
                profile_override=profile,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key_override=api_key_override
            ):
                if chunk.get("provider"):
                    actual_provider = chunk["provider"]
                if chunk.get("model"):
                    actual_model = chunk["model"]
                if chunk.get("delta"):
                    total_text.append(chunk["delta"])
                chunk["content"] = chunk.get("delta", "")
                yield f"data: {json.dumps(chunk)}\n\n"

        latency = round((time.perf_counter() - start_time) * 1000, 1)
        tokens_est = round(len("".join(total_text)) / 4)
        AnalyticsTracker.record_request(
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint="/api/chat/stream",
            model=actual_model,
            provider=actual_provider,
            latency_ms=latency,
            status="success",
            tokens_est=tokens_est,
            prompt_snippet=prompt_snippet
        )

        full_answer = "".join(total_text)
        try:
            hardware_bridge.send_answer(prompt_snippet, full_answer, actual_provider, actual_model)
        except Exception:
            pass

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


# -----------------------------------------------------------------------------
# 5. Multi-Model Arena Parallel Broadcast Endpoint
# -----------------------------------------------------------------------------
@app.post("/api/arena/stream")
@app.post("/arena/stream")
async def api_arena_stream(req: ArenaRequest):
    raw_messages = [{"role": m.role, "content": m.content} for m in req.messages]
    prompt_snippet = raw_messages[-1]["content"] if raw_messages else ""

    async def sse_arena_generator():
        queue = asyncio.Queue()
        arena_outputs: Dict[int, List[str]] = {}
        first_provider = "Arena"
        first_model = "Multi-Model"

        async def worker(prov: str, mod: str, worker_id: int):
            arena_outputs[worker_id] = []
            async for chunk in UniversalAdapter.chat_stream(
                provider_id=prov,
                model=mod,
                messages=raw_messages,
                temperature=req.temperature or 0.7,
                max_tokens=req.max_tokens or 2048
            ):
                text_piece = chunk.get("delta", "") or chunk.get("content", "")
                if text_piece and not chunk.get("error"):
                    arena_outputs[worker_id].append(text_piece)
                item = {
                    "arena_worker_id": worker_id,
                    "provider": prov,
                    "model": mod,
                    "delta": text_piece,
                    "content": text_piece,
                    "done": chunk.get("done", False),
                    "latency_ms": chunk.get("latency_ms", 0),
                    "error": chunk.get("error", False)
                }
                await queue.put(item)
            await queue.put({"arena_worker_id": worker_id, "done_all": True})

        # Launch background tasks for each selected model
        tasks = []
        for idx, item in enumerate(req.models):
            prov = item.get("provider", "")
            mod = item.get("model", "")
            if idx == 0 and prov:
                first_provider = prov
                first_model = mod or first_model
            t = asyncio.create_task(worker(prov, mod, idx))
            tasks.append(t)

        completed_workers = 0
        total_workers = len(tasks)

        while completed_workers < total_workers:
            item = await queue.get()
            if item.get("done_all"):
                completed_workers += 1
            else:
                yield f"data: {json.dumps(item)}\n\n"

        full_answer = ""
        for idx in sorted(arena_outputs.keys()):
            candidate = "".join(arena_outputs[idx]).strip()
            if candidate:
                full_answer = candidate
                break

        if full_answer:
            try:
                hardware_bridge.send_answer(prompt_snippet, full_answer, first_provider, first_model)
            except Exception:
                pass

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_arena_generator(), media_type="text/event-stream")


# -----------------------------------------------------------------------------
# 5. IoT & Microcontroller Endpoints (ESP32, ILI9341, Arduino)
# -----------------------------------------------------------------------------
def _clean_for_24inch_tft(raw: str) -> str:
    replacements = {
        "\u2011": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00b2": "^2",
        "\u00b3": "^3",
        "\u00d7": "x",
        "\u00f7": "/",
    }
    for k, v in replacements.items():
        raw = raw.replace(k, v)
    clean = re.sub(r'[*_#`>]', '', raw)
    clean = re.sub(r'\n{3,}', '\n\n', clean).strip()
    return clean


async def _fetch_live_satellite_telemetry() -> str:
    """Fetches real-time orbital satellite telemetry (NORAD #25544 ISS + NOAA SWPC Space Weather)."""
    import httpx
    sat_parts = []
    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            r = await client.get("https://api.wheretheiss.at/v1/satellites/25544")
            if r.status_code == 200:
                d = r.json()
                lat = float(d.get("latitude", 0.0))
                lon = float(d.get("longitude", 0.0))
                alt = float(d.get("altitude", 418.0))
                vel = float(d.get("velocity", 27580.0))
                vis = str(d.get("visibility", "daylight")).upper()
                lat_dir = "N" if lat >= 0 else "S"
                lon_dir = "E" if lon >= 0 else "W"
                sat_parts.append(
                    f"LIVE SATELLITE [ISS NORAD-25544]: Pos {abs(lat):.2f}{lat_dir}, {abs(lon):.2f}{lon_dir} | "
                    f"Alt {alt:.1f}km | Speed {vel:.0f}km/h | Orbit: {vis}"
                )
        except Exception:
            pass

        try:
            r_kp = await client.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json")
            if r_kp.status_code == 200:
                kp_data = r_kp.json()
                if isinstance(kp_data, list) and len(kp_data) > 1:
                    latest = kp_data[-1]
                    kp_val = latest[1]
                    sat_parts.append(f"NOAA Space Weather Kp-Index: {kp_val}")
        except Exception:
            pass

    return " | ".join(sat_parts)


async def _fetch_wikipedia_world_knowledge(query: str) -> str:
    """Fetches verified global world knowledge from Wikipedia's 6.8M-article REST & Search APIs."""
    import httpx
    headers = {"User-Agent": "GenesisGPT4oOmni/5.0 (ESP32-C5 Sovereign Terminal)"}
    async with httpx.AsyncClient(timeout=2.2, headers=headers, follow_redirects=True) as client:
        try:
            sr = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "srlimit": 1, "format": "json"}
            )
            if sr.status_code == 200:
                items = sr.json().get("query", {}).get("search", [])
                if items:
                    title = items[0]["title"]
                    from urllib.parse import quote
                    sm = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}")
                    if sm.status_code == 200:
                        ext = sm.json().get("extract", "").strip()
                        if ext:
                            return _clean_for_24inch_tft(ext)
        except Exception:
            pass
    return ""


_IOT_CHAT_HISTORY: List[Dict[str, str]] = []


async def _fetch_live_web_and_wiki_context(query: str) -> str:
    """Fetches real-time facts from Wikipedia + DuckDuckGo Instant Answer API concurrently."""
    import httpx
    from urllib.parse import quote
    headers = {"User-Agent": "GenesisGPT4oOmni/5.0 (ESP32-C5 Sovereign Terminal)"}

    async def get_wiki() -> str:
        async with httpx.AsyncClient(timeout=2.0, headers=headers, follow_redirects=True) as client:
            try:
                sr = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={"action": "query", "list": "search", "srsearch": query, "srlimit": 1, "format": "json"}
                )
                if sr.status_code == 200:
                    items = sr.json().get("query", {}).get("search", [])
                    if items:
                        title = items[0]["title"]
                        sm = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}")
                        if sm.status_code == 200:
                            ext = sm.json().get("extract", "").strip()
                            if ext:
                                return _clean_for_24inch_tft(ext)
            except Exception:
                pass
        return ""

    async def get_ddg() -> str:
        async with httpx.AsyncClient(timeout=1.8, headers=headers, follow_redirects=True) as client:
            try:
                dr = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
                )
                if dr.status_code == 200:
                    d = dr.json()
                    ans = (d.get("Answer") or d.get("AbstractText") or d.get("Definition") or "").strip()
                    if ans:
                        return _clean_for_24inch_tft(str(ans))
            except Exception:
                pass
        return ""

    w_task = asyncio.create_task(get_wiki())
    d_task = asyncio.create_task(get_ddg())
    res_w, res_d = await asyncio.gather(w_task, d_task, return_exceptions=True)
    parts = []
    if isinstance(res_d, str) and res_d:
        parts.append(res_d)
    if isinstance(res_w, str) and res_w and res_w not in parts:
        parts.append(res_w)
    return " | ".join(parts)


@app.get("/api/iot/satellite")
async def iot_satellite_endpoint():
    sat = await _fetch_live_satellite_telemetry()
    if not sat:
        sat = "LIVE SATELLITE [NORAD-25544]: Orbital link active | Alt 418.2km | Speed 27580km/h"
    return Response(content=sat, media_type="text/plain; charset=utf-8")


async def _fast_race_iot_llm(raw_messages: List[Dict[str, str]], max_words: int = 52) -> str:
    """Races multiple fast LLM backends concurrently so IoT devices always get a fast response."""
    import httpx
    or_key = GatewayConfig.get_key("OPENROUTER_API_KEY")
    gem_key = GatewayConfig.get_key("GEMINI_API_KEY") or GatewayConfig.get_key("GEMINI_BACKUP_KEY")
    is_cloud = _is_cloud_env()

    async def call_or_model(model_id: str, fallback_models: Optional[List[str]] = None) -> str:
        if not or_key:
            return ""
        payload: Dict[str, Any] = {
            "reasoning": {"exclude": True},
            "messages": raw_messages,
            "temperature": 0.4
        }
        if fallback_models:
            payload["models"] = fallback_models
        else:
            payload["model"] = model_id

        try:
            async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                    json=payload
                )
                if r.status_code == 200:
                    txt = (r.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if len(txt) > 2:
                        return txt
                elif r.status_code in (402, 429):
                    return ""
        except Exception:
            pass
        return ""

    async def call_gemini() -> str:
        if not gem_key:
            return ""
        try:
            sys_text = next((m["content"] for m in raw_messages if m.get("role") == "system"), "")
            gem_contents = [
                {"role": "user" if m.get("role") == "user" else "model", "parts": [{"text": m.get("content", "")}]}
                for m in raw_messages if m.get("role") != "system"
            ]
            payload: Dict[str, Any] = {
                "contents": gem_contents,
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 256}
            }
            if sys_text:
                payload["systemInstruction"] = {"parts": [{"text": sys_text}]}
            async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={gem_key}",
                    json=payload
                )
                if r.status_code == 200:
                    cands = r.json().get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        txt = "".join(p.get("text", "") for p in parts).strip()
                        if len(txt) > 2:
                            return txt
        except Exception:
            pass
        return ""

    async def call_local_ollama() -> str:
        if is_cloud:
            return ""
        try:
            async with httpx.AsyncClient(timeout=4.5) as client:
                r = await client.post(
                    "http://127.0.0.1:11434/v1/chat/completions",
                    json={"model": "llama3.2:1b", "messages": raw_messages, "temperature": 0.4}
                )
                if r.status_code == 200:
                    txt = (r.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if len(txt) > 2:
                        return txt
                elif r.status_code in (402, 429):
                    return ""
        except Exception:
            pass
        return ""

    async def call_pollinations() -> str:
        if or_key or gem_key or not is_cloud:
            await asyncio.sleep(0.35)
        try:
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                r = await client.post(
                    "https://text.pollinations.ai/openai",
                    headers={"Content-Type": "application/json"},
                    json={"model": "openai", "messages": raw_messages, "temperature": 0.4, "stream": False}
                )
                if r.status_code == 200:
                    txt = (r.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if len(txt) > 2:
                        return txt
                elif r.status_code in (402, 429):
                    return ""
        except Exception:
            pass
        try:
            import urllib.parse
            last_q = next((m["content"] for m in reversed(raw_messages) if m.get("role") == "user"), "Hello")
            async with httpx.AsyncClient(timeout=7.0, verify=False) as client:
                r_get = await client.get(f"https://text.pollinations.ai/{urllib.parse.quote(last_q)}")
                if r_get.status_code == 200:
                    txt = r_get.text.strip()
                    if len(txt) > 2:
                        return txt
        except Exception:
            pass
        return ""

    tasks = [
        asyncio.create_task(call_local_ollama()),
        asyncio.create_task(call_gemini()),
        asyncio.create_task(call_or_model("nvidia/nemotron-3-ultra-550b-a55b:free")),
        asyncio.create_task(call_or_model("openrouter/free")),
        asyncio.create_task(call_pollinations()),
    ]
    winner_text = ""
    try:
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=8.5)
            if not done:
                break
            for d in done:
                try:
                    res = d.result()
                    if res and len(res.strip()) > 2:
                        winner_text = res.strip()
                        break
                except Exception:
                    pass
            if winner_text:
                for p in pending:
                    p.cancel()
                break
            tasks = list(pending)
    except Exception:
        pass
    return winner_text


@app.get("/api/iot/chat")
@app.get("/api/iot/chat/")
@app.post("/api/iot/chat")
@app.post("/api/iot/chat/")
async def iot_chat_endpoint(
    request: Request,
    q: Optional[str] = None,
    max_words: int = 52,
    format: Optional[str] = None
):
    global _IOT_CHAT_HISTORY
    user_prompt = q
    if not user_prompt and request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                user_prompt = body.get("prompt") or body.get("q") or body.get("message")
            elif isinstance(body, str):
                user_prompt = body
        except Exception:
            pass
    user_prompt = (user_prompt or "Hello").strip()
    lower_q = user_prompt.lower()

    # Instant mirror thinking state to 2.4-inch physical screen
    try:
        hardware_bridge.send_thinking(user_prompt, "relay", "GENESIS AI")
    except Exception:
        pass

    if lower_q in ["clear", "reset", "new chat", "clear history"]:
        _IOT_CHAT_HISTORY.clear()
        msg = "Conversation memory cleared! Ask me anything on any topic."
        if format == "json":
            return {"prompt": user_prompt, "text": msg, "length": len(msg)}
        return Response(content=msg, media_type="text/plain; charset=utf-8")

    sat_keywords = ["satellite", "iss", "space station", "orbit", "norad", "telemetry", "space weather", "solar storm", "noaa", "where is the iss", "astronaut"]
    is_sat_query = any(k in lower_q for k in sat_keywords)

    live_sat_info = ""
    if is_sat_query:
        live_sat_info = await _fetch_live_satellite_telemetry()
        if live_sat_info and any(k in lower_q for k in ["satellite", "iss", "telemetry", "orbit", "space station"]):
            clean_sat = _clean_for_24inch_tft(live_sat_info)
            if format == "json":
                return {"prompt": user_prompt, "text": clean_sat, "length": len(clean_sat)}
            return Response(content=clean_sat, media_type="text/plain; charset=utf-8")

    # Start live Web + Wikipedia grounding task; wait up to 0.85s upfront so factual answers are grounded!
    web_task = asyncio.create_task(_fetch_live_web_and_wiki_context(user_prompt))
    wiki_context = ""
    done_w, _ = await asyncio.wait([web_task], timeout=0.85)
    if done_w:
        try:
            wiki_context = web_task.result()
        except Exception:
            wiki_context = ""

    from datetime import datetime
    now_str = datetime.now().strftime("%A, %B %d, %Y %I:%M %p IST")

    context_block = f" Current Date & Time: {now_str}."
    if live_sat_info:
        context_block += f" Live Real-Time Satellite Telemetry: {live_sat_info}."
    if wiki_context:
        words = wiki_context.split()
        short_wiki = " ".join(words[:70])
        context_block += f" Live Factual Reference: {short_wiki}."

    raw_messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"You are GENESIS GPT-4o OMNI, an omniscient ChatGPT-class AI assistant created by Ishit Jain, running on an ESP32-C5 with a 320x240 display. "
                f"You can answer ANY question across science, coding, math, history, geography, current events, translations, stories, advice, and satellite telemetry. "
                f"Respond directly, accurately, and completely in {max_words} words or fewer using plain ASCII text with no markdown or asterisks."
                f"{context_block}"
            )
        }
    ]
    # Include rolling multi-turn conversation history (last 4 messages = 2 turns) for ChatGPT follow-ups!
    for h in _IOT_CHAT_HISTORY[-4:]:
        raw_messages.append(h)
    raw_messages.append({"role": "user", "content": user_prompt})

    raw_response = await _fast_race_iot_llm(raw_messages, max_words=max_words)
    clean = _clean_for_24inch_tft(raw_response)

    if not clean or "All providers failed" in clean or "Provider Error" in clean or len(clean) < 4:
        if not wiki_context:
            try:
                wiki_context = await asyncio.wait_for(web_task, timeout=2.0)
            except Exception:
                wiki_context = ""
        if wiki_context:
            w_words = wiki_context.split()
            clean = " ".join(w_words[:max_words])
            if len(w_words) > max_words:
                clean += "..."
        else:
            clean = _clean_for_24inch_tft(SmartRouter.generate_uninterrupted_fallback(user_prompt))
    else:
        if not web_task.done():
            web_task.cancel()

    if clean and len(clean) > 3:
        _IOT_CHAT_HISTORY.append({"role": "user", "content": user_prompt})
        _IOT_CHAT_HISTORY.append({"role": "assistant", "content": clean})
        if len(_IOT_CHAT_HISTORY) > 8:
            _IOT_CHAT_HISTORY = _IOT_CHAT_HISTORY[-8:]

    # Push final response to physical 2.4-inch display
    try:
        hardware_bridge.send_answer(user_prompt, clean, "relay", "GENESIS AI")
    except Exception:
        pass

    if format == "json":
        return {
            "prompt": user_prompt,
            "text": clean,
            "length": len(clean)
        }

    return Response(content=clean, media_type="text/plain; charset=utf-8")


@app.post("/api/screen/push")
@app.get("/api/screen/push")
async def push_screen_endpoint(request: Request, q: Optional[str] = None, text: Optional[str] = None, state: str = "ANSWERED", model: str = "GENESIS AI", provider: str = "relay"):
    body = {}
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            pass
    question = q or body.get("question") or body.get("q") or body.get("prompt") or ""
    answer = text or body.get("text") or body.get("answer") or ""
    cur_state = body.get("state") or state
    cur_model = body.get("model") or model
    cur_prov = body.get("provider") or provider

    try:
        if cur_state == "THINKING":
            hardware_bridge.send_thinking(question, cur_prov, cur_model)
        else:
            hardware_bridge.send_answer(question, answer, cur_prov, cur_model)
        return {"status": "ok", "screen_synced": True, "bridge_info": hardware_bridge.get_status()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/screen/status")
async def screen_status_endpoint():
    return hardware_bridge.get_status()


@app.get("/api/screen/poll")
async def screen_poll_endpoint(v: int = 0):
    feed = hardware_bridge.latest_feed
    if v == feed.get("version", 0):
        return {"changed": False, "version": feed.get("version", 0)}
    return {
        "changed": True,
        **feed
    }


@app.post("/api/screen/register")
async def screen_register_endpoint(request: Request):
    try:
        body = await request.json()
        ip = body.get("ip") or body.get("esp_ip")
        if ip:
            hardware_bridge.esp_wifi_ip = ip
            hardware_bridge._wifi_ok = True
            return {"status": "ok", "registered_ip": ip}
    except Exception:
        pass
    return {"status": "error", "detail": "missing IP"}


@app.get("/api/system/resources")
async def system_resources_endpoint():
    import httpx
    is_cloud = _is_cloud_env()
    online = SmartRouter.check_internet()

    ollama_info = {"status": "cloud_disabled" if is_cloud else "stopped", "models": []}
    if not is_cloud:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                r = await client.get("http://127.0.0.1:11434/api/tags")
                if r.status_code == 200:
                    models = [m.get("name") for m in r.json().get("models", [])]
                    ollama_info = {"status": "running", "models": models}
        except Exception:
            pass

    disk_target = "C:\\" if sys.platform == "win32" else "/"
    try:
        disk = shutil.disk_usage(disk_target)
        disk_free_gb = round(disk.free / (1024**3), 1)
        disk_total_gb = round(disk.total / (1024**3), 1)
    except Exception:
        disk_free_gb = 0.0
        disk_total_gb = 0.0

    if psutil is not None:
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024**3), 1)
        ram_available_gb = round(mem.available / (1024**3), 1)
        cpu_phys = psutil.cpu_count(logical=False)
        cpu_log = psutil.cpu_count(logical=True)
        cpu_pct = psutil.cpu_percent()
    else:
        ram_total_gb = 0.0
        ram_available_gb = 0.0
        cpu_phys = os.cpu_count() or 1
        cpu_log = os.cpu_count() or 1
        cpu_pct = 0.0

    rec_model = "openai (Pollinations Cloud)" if is_cloud else "llama3.2:1b"
    rec_reason = (
        "Serverless Cloud Gateway active with zero-key frontier routing."
        if is_cloud
        else "1.3GB lightweight model, optimal for current available system RAM."
    )

    return {
        "status": "ok",
        "cloud_mode": is_cloud,
        "internet_connected": online,
        "mode": "CLOUD FRONTIER GATEWAY" if is_cloud else ("ONLINE DUAL BRAIN" if online else "OFFLINE LOCAL BRAIN"),
        "ollama": ollama_info,
        "recommended_model": rec_model,
        "recommendation_reason": rec_reason,
        "resources": {
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_available_gb,
            "cpu_physical_cores": cpu_phys,
            "cpu_logical_cores": cpu_log,
            "cpu_percent": cpu_pct,
            "disk_free_gb": disk_free_gb,
            "disk_total_gb": disk_total_gb
        },
        "screen_bridge": hardware_bridge.get_status()
    }


def main():
    import uvicorn

    port = GatewayConfig.PORT
    host = GatewayConfig.HOST
    if not _is_cloud_env() and hardware_bridge is not None:
        hardware_bridge.start_background_tasks()
    print("==================================================================")
    print(f"🚀 OmniModel Universal AI Gateway starting on http://{host}:{port}")
    print(f"📡 OpenAI Proxy endpoint ready at http://{host}:{port}/v1/chat/completions")
    print(f"🌐 Web Dashboard & Multi-Model Arena ready at http://{host}:{port}/")
    print("==================================================================")
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
