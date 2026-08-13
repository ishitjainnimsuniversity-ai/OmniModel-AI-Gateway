"""
OmniModel AI Universal Gateway Server
Serves OpenAI-compatible proxy, multi-model arena, smart routing, and web dashboard.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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

from core.config import GatewayConfig
from core.providers import PROVIDERS_METADATA
from core.adapters import UniversalAdapter
from core.router import SmartRouter
from core.analytics import AnalyticsTracker

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

# Mount static files
PUBLIC_DIR = BASE_DIR / "public"
PUBLIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

@app.get("/style.css")
async def get_style_css():
    css_path = PUBLIC_DIR / "style.css"
    if css_path.exists():
        from fastapi.responses import Response
        return Response(content=css_path.read_text(encoding="utf-8"), media_type="text/css")
    return Response(content="", media_type="text/css")

@app.get("/app.js")
async def get_app_js():
    js_path = PUBLIC_DIR / "app.js"
    if js_path.exists():
        from fastapi.responses import Response
        return Response(content=js_path.read_text(encoding="utf-8"), media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

@app.get("/logo.png")
async def get_logo_png():
    from fastapi.responses import FileResponse
    logo_path = PUBLIC_DIR / "logo.png"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "logo not found"})

@app.get("/ai_bg.jpg")
async def get_ai_bg_jpg():
    from fastapi.responses import FileResponse
    bg_path = PUBLIC_DIR / "ai_bg.jpg"
    if bg_path.exists():
        return FileResponse(str(bg_path), media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"error": "bg not found"})

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
    env_var: str
    value: str

class ArenaRequest(BaseModel):
    models: List[Dict[str, str]] # [{"provider": "groq", "model": "llama-3.3-70b-versatile"}, ...]
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

# -----------------------------------------------------------------------------
# 1. Web Dashboard Delivery
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = PUBLIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>OmniModel Gateway UI Loading...</h1>"

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
async def get_providers():
    status = GatewayConfig.get_active_providers_status(PROVIDERS_METADATA)
    return {"success": True, "providers": status, "total": len(status)}

@app.get("/api/analytics")
async def get_user_analytics():
    """Returns analytics of users and requests who have used the app"""
    summary = AnalyticsTracker.get_summary()
    return {"success": True, "analytics": summary}

@app.post("/api/analytics/clear")
async def clear_user_analytics():
    AnalyticsTracker.clear_records()
    return {"success": True, "message": "Analytics history cleared"}

@app.post("/api/keys")
async def update_api_key(req: KeyUpdateRequest):
    success = GatewayConfig.set_key(req.env_var, req.value.strip())
    if success:
        return {"success": True, "message": f"Successfully updated {req.env_var}"}
    raise HTTPException(status_code=500, detail="Failed to write key to .env")

@app.post("/api/ping/{provider_id}")
async def ping_provider(provider_id: str):
    result = await UniversalAdapter.test_ping(provider_id)
    return result

# -----------------------------------------------------------------------------
# 4. Interactive Dashboard SSE Streaming Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/chat/stream")
async def api_chat_stream(
    request: Request,
    messages: List[ChatMessage] = Body(...),
    provider: Optional[str] = Body(None),
    model: Optional[str] = Body(None),
    profile: Optional[str] = Body(None),
    temperature: float = Body(0.7),
    max_tokens: int = Body(2048)
):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "Web-Browser")
    raw_messages = [{"role": m.role, "content": m.content} for m in messages]
    prompt_snippet = raw_messages[-1]["content"] if raw_messages else ""
    start_time = time.perf_counter()

    async def sse_generator():
        total_text = []
        actual_provider = provider or "router"
        actual_model = model or "auto"

        if provider and provider != "auto":
            target_model = model or PROVIDERS_METADATA.get(provider, {}).get("default_model", "")
            async for chunk in UniversalAdapter.chat_stream(
                provider_id=provider,
                model=target_model,
                messages=raw_messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if chunk.get("delta"):
                    total_text.append(chunk["delta"])
                yield f"data: {json.dumps(chunk)}\n\n"
        else:
            async for chunk in SmartRouter.route_and_execute_stream(
                messages=raw_messages,
                profile_override=profile,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if chunk.get("provider"):
                    actual_provider = chunk["provider"]
                if chunk.get("model"):
                    actual_model = chunk["model"]
                if chunk.get("delta"):
                    total_text.append(chunk["delta"])
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

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# -----------------------------------------------------------------------------
# 5. Multi-Model Arena Parallel Broadcast Endpoint
# -----------------------------------------------------------------------------
@app.post("/api/arena/stream")
async def api_arena_stream(req: ArenaRequest):
    raw_messages = [{"role": m.role, "content": m.content} for m in req.messages]
    
    async def sse_arena_generator():
        queue = asyncio.Queue()

        async def worker(prov: str, mod: str, worker_id: int):
            async for chunk in UniversalAdapter.chat_stream(
                provider_id=prov,
                model=mod,
                messages=raw_messages,
                temperature=req.temperature or 0.7,
                max_tokens=req.max_tokens or 2048
            ):
                item = {
                    "arena_worker_id": worker_id,
                    "provider": prov,
                    "model": mod,
                    "delta": chunk.get("delta", ""),
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

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_arena_generator(), media_type="text/event-stream")

def main():
    port = GatewayConfig.PORT
    host = GatewayConfig.HOST
    print("==================================================================")
    print(f"🚀 OmniModel Universal AI Gateway starting on http://{host}:{port}")
    print(f"📡 OpenAI Proxy endpoint ready at http://{host}:{port}/v1/chat/completions")
    print(f"🌐 Web Dashboard & Multi-Model Arena ready at http://{host}:{port}/")
    print("==================================================================")
    uvicorn.run("server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
