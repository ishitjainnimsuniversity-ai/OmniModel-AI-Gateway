"""GENESIS AI — Local Testing HTTPS/HTTP Relay Service.
Run with: python local_relay.py
Provides /api/chat with streaming response from Gemini or mock.
"""
import os
import json
import uvicorn
import urllib.parse
import random
import uuid
import base64
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

app = FastAPI(title="GENESIS AI Local Relay")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "GENESIS AI Local Relay",
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/image/generate")
async def generate_image(request: Request):
    body = await request.json()
    prompt = (body.get("prompt") or "").strip()
    style = body.get("style") or "Photorealistic"
    aspect = body.get("aspect_ratio") or "1:1"

    if not prompt:
        return JSONResponse({"error": "Empty prompt"}, status_code=400)

    dims = {
        "1:1": (512, 512),
        "16:9": (768, 432),
        "9:16": (432, 768),
        "4:3": (640, 480),
        "3:4": (480, 640)
    }.get(aspect, (512, 512))

    style_prompts = {
        "Photorealistic": "photorealistic, 8k raw photography, hyper-detailed, studio lighting",
        "Anime / Manga": "anime aesthetic, clean linework, vibrant makoto shinkai style, illustration",
        "Cyberpunk": "cyberpunk style, neon lights, rainy reflections, futuristic cityscape, octane render",
        "Cinematic": "cinematic film still, 35mm photograph, dramatic movie lighting",
        "Digital Art": "digital art masterpiece, trending on artstation, intricate concept art",
        "Dark Fantasy": "dark fantasy, dramatic shadows, mysterious glowing runes, fog, unreal engine 5",
        "Watercolor": "delicate watercolor painting, artistic pigment bleeding, textured paper",
        "3D Render": "3d octane render, ray tracing, smooth textures, subsurface scattering, 8k cgi"
    }

    mod = style_prompts.get(style, "")
    full_prompt = f"{prompt}, {mod}" if mod else prompt
    seed = random.randint(1, 999999)
    gen_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(full_prompt)}?width={dims[0]}&height={dims[1]}&seed={seed}&model=flux&nologo=true"

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.get(gen_url)
        if resp.status_code != 200:
            return JSONResponse({"error": f"Image provider HTTP {resp.status_code}"}, status_code=resp.status_code)

        img_b64 = base64.b64encode(resp.content).decode("ascii")
        return {
            "ok": True,
            "request_id": f"img_{uuid.uuid4().hex[:8]}",
            "image_url": f"data:image/jpeg;base64,{img_b64}",
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect,
            "width": dims[0],
            "height": dims[1]
        }

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = (body.get("message") or "").strip()
    model = body.get("model") or "gemini-2.5-flash"
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not message:
        return JSONResponse({"error": "Empty prompt"}, status_code=400)

    if not api_key:
        return JSONResponse({"error": "GEMINI_API_KEY not configured in .env"}, status_code=500)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }

    async def sse_gen():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    err_text = await resp.aread()
                    yield f"data: {json.dumps({'error': f'Upstream HTTP {resp.status_code}'})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.strip() or not line.startswith("data:"):
                        continue
                    try:
                        raw = json.loads(line[5:].strip())
                        cands = raw.get("candidates") or []
                        if cands:
                            parts = cands[0].get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)
                            if text:
                                yield f"data: {json.dumps({'delta': text})}\n\n"
                    except Exception:
                        pass
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_gen(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)
