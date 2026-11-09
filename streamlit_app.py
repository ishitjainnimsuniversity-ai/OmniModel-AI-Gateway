"""
GENESIS AI 5.0 // Universal Cognitive Neural Interface (Streamlit Cloud + Local Dual-Brain Edition)
Full Feature Parity with OmniModel AI Gateway + Tri-Channel 2.4-inch ESP32-C5 Screen Communication.
Created by Ishit Jain.
"""

from __future__ import annotations

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import html as html_lib
import importlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
import uuid

import httpx
import pandas as pd
import streamlit as st

try:
    import streamlit.components.v1 as components
except Exception:
    components = None


def _render_html_component(html_str: str, height: int = 120, width: Optional[int] = None) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_str, height=max(1, height), width=width if (width and width > 0) else "stretch")
    elif components is not None:
        components.html(html_str, height=height, width=width or 0)

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

IS_STREAMLIT_CLOUD = bool(
    os.getenv("STREAMLIT_SHARING_MODE")
    or os.getenv("IS_CLOUD_RUNTIME") == "1"
    or os.getenv("GENESIS_CLOUD_MODE") == "1"
    or os.path.exists("/mount/src")
    or (sys.platform.startswith("linux") and Path.home().name == "adminuser")
)
if IS_STREAMLIT_CLOUD:
    os.environ["GENESIS_CLOUD_MODE"] = "1"

import core.config as _core_config  # noqa: E402
import core.providers as _core_providers  # noqa: E402
import core.adapters as _core_adapters  # noqa: E402
import core.router as _core_router  # noqa: E402
from core.analytics import AnalyticsTracker  # noqa: E402
from core.screen_bridge import hardware_bridge  # noqa: E402

# Ensure soft-pulls on Streamlit Cloud reload updated core modules in long-lived worker processes
_CORE_MTIMES = tuple(
    (BASE_DIR / "core" / fname).stat().st_mtime
    for fname in ("config.py", "providers.py", "adapters.py", "router.py")
)
if (
    getattr(sys, "_genesis_core_mtimes", None) != _CORE_MTIMES
    or not hasattr(_core_router.SmartRouter, "generate_uninterrupted_fallback_meta")
):
    if getattr(sys, "_genesis_core_mtimes", None) is not None or not hasattr(_core_router.SmartRouter, "generate_uninterrupted_fallback_meta"):
        _core_config = importlib.reload(_core_config)
        _core_providers = importlib.reload(_core_providers)
        _core_adapters = importlib.reload(_core_adapters)
        _core_router = importlib.reload(_core_router)
    sys._genesis_core_mtimes = _CORE_MTIMES  # type: ignore[attr-defined]

GatewayConfig = _core_config.GatewayConfig
PROVIDERS_METADATA = _core_providers.PROVIDERS_METADATA
UniversalAdapter = _core_adapters.UniversalAdapter
SmartRouter = _core_router.SmartRouter


# ---------------------------------------------------------------------------
# 1. Host Secrets Hydration (Never Exposed to Client Sessions)
# ---------------------------------------------------------------------------
def _hydrate_host_secrets() -> None:
    try:
        secrets_obj = st.secrets
        for key in list(secrets_obj.keys()):
            val = secrets_obj[key]
            if isinstance(val, str) and val.strip():
                os.environ.setdefault(key, val.strip())
            elif isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    if isinstance(sub_v, str) and sub_v.strip():
                        os.environ.setdefault(str(sub_k), sub_v.strip())
    except Exception:
        pass


_hydrate_host_secrets()

LOGO_PATH = BASE_DIR / "public" / "assistant_logo.png"
if not LOGO_PATH.exists():
    LOGO_PATH = BASE_DIR / "logo.png"

st.set_page_config(
    page_title="GENESIS AI 5.0 // Universal Cognitive Neural Interface",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# 2. Safe Async Executor & Shared Runtime State
# ---------------------------------------------------------------------------
_THREAD_POOL = ThreadPoolExecutor(max_workers=6)


def run_async(coro):
    try:
        asyncio.get_running_loop()
        return _THREAD_POOL.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


@st.cache_resource
def get_shared_screen_state() -> Dict[str, Any]:
    return {
        "lock": threading.Lock(),
        "version": 1,
        "cmd_id": "init",
        "state": "READY",
        "question": "Awaiting prompt from GENESIS AI 5.0...",
        "answer": "Ready for multimodal reasoning, live search, swarm debate, or Flux Art streaming.",
        "provider": "Pollinations / SmartRouter",
        "model": "GENESIS AI 5.0",
        "latency_ms": 0,
        "rgb_brightness": 45,
        "fusion_watermark": True,
        "last_image_url": "",
        "last_image_bytes": None,
        "last_image_prompt": "",
        "updated_at": time.strftime("%H:%M:%S"),
        "sync_log": [],
    }


@st.cache_resource
def start_local_bridge_once() -> bool:
    if not IS_STREAMLIT_CLOUD:
        try:
            hardware_bridge.cloud_mode = False
            hardware_bridge.start_background_tasks()
            return True
        except Exception:
            return False
    return False


start_local_bridge_once()


def _logo_b64() -> str:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return ""


# ---------------------------------------------------------------------------
# 3. Themes & Cybernetic CSS Injection
# ---------------------------------------------------------------------------
THEMES: Dict[str, Dict[str, str]] = {
    "Quantum Cyan": {"accent": "#00f0ff", "secondary": "#8b5cf6", "glow": "rgba(0,240,255,0.22)"},
    "Matrix Emerald": {"accent": "#10b981", "secondary": "#06b6d4", "glow": "rgba(16,185,129,0.22)"},
    "Solaris Gold": {"accent": "#f59e0b", "secondary": "#ec4899", "glow": "rgba(245,158,11,0.22)"},
    "Crimson Cyber": {"accent": "#f43f5e", "secondary": "#8b5cf6", "glow": "rgba(244,63,94,0.22)"},
    "Glacier Frost": {"accent": "#38bdf8", "secondary": "#6366f1", "glow": "rgba(56,189,248,0.22)"},
}


def init_session_state() -> None:
    if "chats" not in st.session_state:
        first_id = f"chat_{uuid.uuid4().hex[:8]}"
        st.session_state.chats = {
            first_id: {
                "id": first_id,
                "title": "New GENESIS Session",
                "messages": [],
                "created_at": time.strftime("%H:%M"),
            }
        }
        st.session_state.current_chat_id = first_id

    if "workspace" not in st.session_state:
        st.session_state.workspace = "💬 ChatGPT Chat"
    if "theme_name" not in st.session_state:
        st.session_state.theme_name = "Quantum Cyan"
    if "user_keys" not in st.session_state:
        st.session_state.user_keys = {}
    if "mirror_screen" not in st.session_state:
        st.session_state.mirror_screen = True
    if "relay_sync" not in st.session_state:
        st.session_state.relay_sync = True
    if "cloud_relay_url" not in st.session_state:
        st.session_state.cloud_relay_url = os.getenv(
            "GENESIS_CLOUD_RELAY", "https://omni-model-ai-gateway.vercel.app"
        )
    if "local_gateway_url" not in st.session_state:
        st.session_state.local_gateway_url = "http://127.0.0.1:8000"
    if "esp_ip" not in st.session_state:
        st.session_state.esp_ip = "10.33.110.73"
    if "pending_js_cmds" not in st.session_state:
        st.session_state.pending_js_cmds = []
    if "ping_results" not in st.session_state:
        st.session_state.ping_results = {}
    if "arena_results" not in st.session_state:
        st.session_state.arena_results = []
    if "session_analytics" not in st.session_state:
        st.session_state.session_analytics = []
    if "last_tok_speed" not in st.session_state:
        st.session_state.last_tok_speed = 0
    if "pending_starter_prompt" not in st.session_state:
        st.session_state.pending_starter_prompt = None
    if "direct_browser_esp" not in st.session_state:
        st.session_state.direct_browser_esp = False
    if "present_screen_dock" not in st.session_state:
        st.session_state.present_screen_dock = True


init_session_state()

active_theme = THEMES.get(st.session_state.theme_name, THEMES["Quantum Cyan"])
ACCENT = active_theme["accent"]
ACCENT2 = active_theme["secondary"]
GLOW = active_theme["glow"]

st.markdown(
    f"""
<style>
:root {{
  --gen-accent: {ACCENT};
  --gen-accent2: {ACCENT2};
  --gen-glow: {GLOW};
}}
.stApp {{
  background: radial-gradient(1200px 600px at 55% -10%, #0d1d3a 0%, #030712 65%);
  color: #e6f1ff;
}}
section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #070d1c 0%, #040814 100%);
  border-right: 1px solid rgba(0, 240, 255, 0.16);
}}
.gen-hero {{
  background: linear-gradient(135deg, rgba(11, 20, 38, 0.92), rgba(16, 30, 56, 0.72));
  border: 1px solid {ACCENT}44;
  box-shadow: 0 0 28px {GLOW};
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 14px;
}}
.gen-card {{
  background: rgba(11, 20, 38, 0.85);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 10px;
}}
.gen-badge {{
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid {ACCENT};
  color: {ACCENT};
  background: rgba(0, 240, 255, 0.08);
}}
.gen-pill-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}}
div.stButton > button {{
  border-radius: 10px;
  border: 1px solid rgba(56, 189, 248, 0.25);
  transition: all 0.15s ease;
}}
div.stButton > button:hover {{
  border-color: {ACCENT};
  box-shadow: 0 0 12px {GLOW};
}}
@keyframes genesisChromaBar {{
  0%   {{ background-position: 0% 50%; }}
  50%  {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}
.gen-chroma-bar {{
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #ff1e56, #006bff, #00e5ff, #00d878, #006bff);
  background-size: 300% 100%;
  animation: genesisChromaBar 5s ease infinite;
  margin-bottom: 8px;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# 4. Utilities: Keys, Clean TFT Text, RGB565 Encoder, Tri-Channel ESP32 Sync
# ---------------------------------------------------------------------------
def _clean_for_tft(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<thought>[\s\S]*?</thought>", "", raw, flags=re.IGNORECASE)
    for k, v in {
        "\u2011": "-", "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00b2": "^2", "\u00b3": "^3",
    }.items():
        text = text.replace(k, v)
    text = re.sub(r"[*_#`>]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def get_resolved_key(env_var: Optional[str]) -> Optional[str]:
    if not env_var:
        return None
    sess_val = (st.session_state.user_keys.get(env_var) or "").strip()
    if sess_val:
        return sess_val
    return GatewayConfig.get_key(env_var)


def _has_any_api_key() -> bool:
    for pid, meta in PROVIDERS_METADATA.items():
        if pid in ("ollama", "pollinations"):
            continue
        ev = meta.get("env_var")
        if ev and get_resolved_key(ev):
            return True
    return False


def _build_tft_bezel_html(shared: Dict[str, Any], esp_ip: str, compact: bool = False) -> str:
    with shared["lock"]:
        cur_state = shared["state"]
        cur_q = shared["question"]
        cur_ans = shared["answer"]
        cur_prov = shared["provider"]
        cur_mod = shared["model"]
        cur_rgb = shared["rgb_brightness"]
        cur_fw = shared["fusion_watermark"]
        cur_img = shared.get("last_image_bytes")

    logo_b64 = _logo_b64()
    bg_watermark = (
        f"background-image:url('data:image/png;base64,{logo_b64}');opacity:0.13;"
        if (cur_fw and logo_b64)
        else "opacity:0;"
    )
    img_preview_html = ""
    if cur_state == "IMAGE_VIEW" and cur_img:
        img_mime = "image/png" if cur_img[:4] == b"\x89PNG" else "image/jpeg"
        img_b64 = base64.b64encode(cur_img).decode("ascii")
        max_h = "110px" if compact else "135px"
        img_preview_html = (
            f'<div style="text-align:center;margin:6px 0;">'
            f'<img src="data:{img_mime};base64,{img_b64}" style="max-height:{max_h};border:1px solid #00f0ff;border-radius:6px;">'
            f'</div>'
        )

    ans_limit = 380 if compact else 560
    ans_display = cur_ans[:ans_limit] + ("..." if len(cur_ans) > ans_limit else "")
    safe_q_html = html_lib.escape(cur_q or "Awaiting input...").replace("\r", "").replace("\n", "<br/>")
    safe_ans_html = html_lib.escape(ans_display or "Ready.").replace("\r", "").replace("\n", "<br/>")

    pad_outer = "12px" if compact else "18px"
    min_h = "230px" if compact else "270px"
    wm_sz = "120px" if compact else "150px"

    pcb_lines = [
        f'<div style="background:linear-gradient(180deg,#5c0b0b,#3a0606);border:2px solid #b91c1c;border-radius:16px;padding:{pad_outer};box-shadow:0 0 28px rgba(239,68,68,0.24);">',
        '<div style="display:flex;justify-content:space-between;font-family:monospace;font-size:10px;color:#fbbf24;margin-bottom:6px;">',
        '<span>VCC GND CS RST DC MOSI SCK</span>',
        '<span>2.4&quot; ILI9341 (320x240)</span>',
        '</div>',
        '<div class="gen-chroma-bar"></div>',
        f'<div style="position:relative;background:#000;border:4px solid #111827;border-radius:8px;min-height:{min_h};display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;font-family:Consolas,monospace;">',
        f'<div style="position:absolute;inset:0;background-position:center;background-size:{wm_sz} {wm_sz};background-repeat:no-repeat;pointer-events:none;{bg_watermark}"></div>',
        '<div style="background:#051c38;border-bottom:2px solid #22d3ee;padding:5px 9px;display:flex;justify-content:space-between;font-size:10px;color:#22d3ee;z-index:2;">',
        '<span>⚡ GENESIS AI 5.0</span>',
        f'<span style="color:#34d399;">{html_lib.escape(str(cur_state))} • {html_lib.escape(str(cur_prov))}</span>',
        '</div>',
        '<div style="padding:8px 10px;flex:1;z-index:2;overflow-y:auto;">',
        '<div style="color:#34d399;font-size:10px;font-weight:700;">▶ PROMPT:</div>',
        f'<div style="color:#a5f3fc;font-size:11px;margin-bottom:6px;">{safe_q_html}</div>',
        img_preview_html,
        f'<div style="color:#fbbf24;font-size:10px;font-weight:700;">✦ GENESIS ANSWER ({html_lib.escape(str(cur_mod))}):</div>',
        f'<div style="color:#f1f5f9;font-size:11px;line-height:1.42;border-left:2px solid #fbbf24;padding-left:8px;">{safe_ans_html}</div>',
        '</div>',
        '<div style="background:#0d1624;border-top:1px solid #334155;padding:4px 9px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;z-index:2;">',
        f'<span>IP: {html_lib.escape(esp_ip)} • RGB GPIO27: {cur_rgb}%</span>',
        '<span style="color:#22d3ee;">RISC-V 240MHz</span>',
        '</div>',
        '</div>',
        '<div style="text-align:center;font-family:monospace;font-size:9px;color:#fbbf24;margin-top:6px;">ESP32-C5 Wi-Fi 6 • GENESIS PHOTON GPIO27 CHROMA • LIVE SYNC</div>',
        '</div>',
    ]
    return "\n".join(p for p in pcb_lines if p)


def encode_image_rgb565_chunks(image_bytes: bytes, aspect: str = "1:1") -> Tuple[int, int, int, int, List[Dict[str, Any]]]:
    if not HAS_PIL:
        raise RuntimeError("Pillow is not available for RGB565 TFT image encoding.")
    aspect_dims = {
        "1:1": (140, 140),
        "16:9": (240, 135),
        "9:16": (84, 150),
        "4:3": (192, 144),
        "3:4": (112, 150),
    }
    tw, th = aspect_dims.get(aspect, (140, 140))
    tx = (320 - tw) // 2
    ty = 54 + (156 - th) // 2

    img = Image.open(BytesIO(image_bytes)).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())

    chunks: List[Dict[str, Any]] = []
    lines_per_chunk = 10
    for y in range(0, th, lines_per_chunk):
        chunk_h = min(lines_per_chunk, th - y)
        buf = bytearray()
        row_start = y * tw
        row_end = (y + chunk_h) * tw
        for r, g, b in pixels[row_start:row_end]:
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf.append((rgb565 >> 8) & 0xFF)
            buf.append(rgb565 & 0xFF)
        chunks.append({
            "x": tx,
            "y": ty + y,
            "w": tw,
            "h": chunk_h,
            "data": base64.b64encode(bytes(buf)).decode("ascii"),
        })
    return tx, ty, tw, th, chunks


def _post_cloud_relay_async(relay_url: str, payload: Dict[str, Any]) -> None:
    if not relay_url:
        return
    base = relay_url.rstrip("/")

    def _worker():
        try:
            with httpx.Client(timeout=3.5) as client:
                client.post(f"{base}/api/screen/command", json=payload)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def dispatch_screen_command(payload: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """
    Updates Shared Screen Simulator AND dispatches across:
      Channel 1: Local HardwareScreenBridge (Wi-Fi LAN / SoftAP / USB COM4 when local)
      Channel 2: Browser JS Loopback (http://127.0.0.1:8000 -> local gateway -> ESP32)
      Channel 3: Cloud Relay (Vercel /api/screen/command -> home PC sync -> ESP32)
    """
    shared = get_shared_screen_state()
    cmd_id = payload.get("cmd_id") or f"{payload.get('action', 'feed')}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:5]}"
    payload["cmd_id"] = cmd_id
    payload.setdefault("target_ip", st.session_state.esp_ip)

    action = payload.get("action", "feed")
    with shared["lock"]:
        shared["version"] += 1
        shared["cmd_id"] = cmd_id
        shared["updated_at"] = time.strftime("%H:%M:%S")
        if action == "feed":
            shared["state"] = payload.get("state", "ANSWERED")
            shared["question"] = payload.get("question", "")
            if payload.get("text"):
                shared["answer"] = _clean_for_tft(payload["text"])
            elif shared["state"] == "THINKING":
                shared["answer"] = "Querying GENESIS Neural Router..."
            shared["provider"] = payload.get("provider", shared["provider"])
            shared["model"] = payload.get("model", shared["model"])
        elif action == "clear":
            shared["state"] = "READY"
            shared["question"] = "Awaiting input..."
            shared["answer"] = "Ready for query."
            shared["last_image_bytes"] = None
            shared["last_image_url"] = ""
        elif action == "rgb":
            shared["rgb_brightness"] = int(payload.get("brightness", 45))
        elif action == "tft_image":
            shared["state"] = "IMAGE_VIEW"
            shared["question"] = payload.get("prompt", "AI Image Studio")

        shared["sync_log"].insert(
            0,
            f"[{shared['updated_at']}] {action.upper()} | {shared['state']} | IP:{st.session_state.esp_ip}",
        )
        shared["sync_log"] = shared["sync_log"][:15]

    if not force and not st.session_state.mirror_screen:
        return {"ok": True, "local_only": True}

    result_info: Dict[str, Any] = {"cmd_id": cmd_id}

    # Channel 1: Direct Local Python Bridge
    if not IS_STREAMLIT_CLOUD:
        try:
            hardware_bridge.set_target_ip(st.session_state.esp_ip)
            result_info["local_bridge"] = hardware_bridge.execute_command(payload)
        except Exception as exc:
            result_info["local_bridge_err"] = str(exc)

    # Channel 2: Browser JS Loopback Bridge (HTTPS -> http://127.0.0.1:8000/api/screen/command)
    js_payload = dict(payload)
    if action == "feed" and js_payload.get("state") == "ANSWERED":
        st.session_state.pending_js_cmds = [
            c for c in st.session_state.pending_js_cmds
            if not (c.get("action") == "feed" and c.get("state") == "THINKING")
        ]
    st.session_state.pending_js_cmds.append(js_payload)

    # Channel 3: Worldwide Cloud Relay
    if st.session_state.relay_sync and st.session_state.cloud_relay_url:
        _post_cloud_relay_async(st.session_state.cloud_relay_url, payload)
        result_info["cloud_relay_dispatched"] = True

    return result_info


def flush_browser_js_bridge() -> None:
    """Executes queued browser->loopback (and optional direct LAN) screen sync calls silently."""
    cmds = st.session_state.get("pending_js_cmds") or []
    if not cmds:
        return
    st.session_state.pending_js_cmds = []
    local_gw = (st.session_state.local_gateway_url or "http://127.0.0.1:8000").rstrip("/")
    esp_ip = (st.session_state.esp_ip or "10.33.110.73").strip()
    direct_lan = bool(st.session_state.direct_browser_esp)
    cmds_json = json.dumps(cmds)

    _render_html_component(
        f"""
<script>
(async () => {{
  const cmds = {cmds_json};
  const gw = {json.dumps(local_gw)};
  const espIp = {json.dumps(esp_ip)};
  const directLan = {json.dumps(direct_lan)};

  for (const cmd of cmds) {{
    try {{
      await fetch(gw + '/api/screen/command', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(cmd)
      }});
    }} catch (e) {{
      try {{
        await fetch('http://localhost:8000/api/screen/command', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify(cmd)
        }});
      }} catch (e2) {{}}
    }}

    if (directLan && espIp) {{
      const base = 'http://' + espIp;
      try {{
        if (cmd.action === 'rgb') {{
          await fetch(base + '/api/rgb?brightness=' + encodeURIComponent(cmd.brightness ?? 45), {{ method: 'POST' }});
        }} else if (cmd.action === 'page') {{
          await fetch(base + '/api/page', {{ method: 'POST' }});
        }} else if (cmd.action === 'clear') {{
          await fetch(base + '/api/clear', {{ method: 'POST' }});
        }} else if (cmd.action === 'tft_image' && Array.isArray(cmd.chunks)) {{
          await fetch(base + '/api/tft/image/start', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{x: cmd.x, y: cmd.y, w: cmd.w, h: cmd.h, prompt: cmd.prompt, style: cmd.style, aspect: cmd.aspect}})
          }});
          for (const ch of cmd.chunks) {{
            await fetch(base + '/api/tft/image/chunk', {{
              method: 'POST',
              headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify(ch)
            }});
          }}
          await fetch(base + '/api/tft/image/finish', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{style: cmd.style, aspect: cmd.aspect}})
          }});
        }} else {{
          await fetch(base + '/api/feed', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
              state: cmd.state || 'ANSWERED',
              question: cmd.question || '',
              provider: cmd.provider || 'Gemini',
              model: cmd.model || 'GENESIS AI',
              text: cmd.text || ''
            }})
          }});
        }}
      }} catch (e) {{}}
    }}
  }}
}})();
</script>
""",
        height=1,
        width=1,
    )


# ---------------------------------------------------------------------------
# 5. Live Web Search, Weather HUD, System Actions, Swarm, Image Studio
# ---------------------------------------------------------------------------
def fetch_live_web_search(query: str) -> Tuple[str, List[Dict[str, str]]]:
    clean_q = re.sub(r"\b(search|google|web|look up|find|latest news)\b", "", query, flags=re.IGNORECASE).strip() or query
    snippets: List[str] = []
    citations: List[Dict[str, str]] = []
    headers = {"User-Agent": "OmniModelGateway/5.0 (https://github.com/ishitjainnimsuniversity-ai/OmniModel-AI-Gateway)"}

    try:
        with httpx.Client(timeout=6.0, headers=headers, follow_redirects=True) as client:
            r_ddg = client.get(
                "https://api.duckduckgo.com/",
                params={"q": clean_q, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            if r_ddg.status_code == 200:
                d = r_ddg.json()
                ans = (d.get("Answer") or d.get("AbstractText") or d.get("Definition") or "").strip()
                if ans:
                    idx = len(citations) + 1
                    src_url = d.get("AbstractURL") or "https://duckduckgo.com/"
                    snippets.append(f"[{idx}] Instant Fact: {ans} ({src_url})")
                    citations.append({"title": d.get("Heading") or "DuckDuckGo Fact", "url": src_url})
                for topic in (d.get("RelatedTopics") or [])[:3]:
                    if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                        idx = len(citations) + 1
                        snippets.append(f"[{idx}] {topic['Text'][:180]} ({topic['FirstURL']})")
                        citations.append({"title": topic["Text"][:48], "url": topic["FirstURL"]})

            r_wk = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": clean_q, "srlimit": 3, "format": "json"},
            )
            if r_wk.status_code == 200:
                for item in r_wk.json().get("query", {}).get("search", [])[:3]:
                    idx = len(citations) + 1
                    title = item.get("title", "Reference")
                    snip = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                    url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
                    snippets.append(f"[{idx}] {title}: {snip} ({url})")
                    citations.append({"title": title, "url": url})
    except Exception:
        pass

    if not snippets:
        return "", []
    ctx = (
        "\n\n[LIVE WEB SEARCH GROUNDING]:\n"
        + "\n".join(snippets)
        + "\nCite relevant findings using [1], [2].\n"
    )
    return ctx, citations


def fetch_weather_hud(city: str) -> Optional[Dict[str, Any]]:
    try:
        with httpx.Client(timeout=6.0) as client:
            geo = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
            ).json()
            results = geo.get("results") or []
            if not results:
                return None
            loc = results[0]
            w = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": loc["latitude"], "longitude": loc["longitude"], "current_weather": "true"},
            ).json()
            cur = w.get("current_weather") or {}
            code = int(cur.get("weathercode", 0))
            cond = "Clear Skies"
            if 1 <= code <= 3:
                cond = "Partly Cloudy"
            elif 45 <= code <= 48:
                cond = "Fog / Mist"
            elif 51 <= code <= 67:
                cond = "Rain Showers"
            elif 71 <= code <= 86:
                cond = "Snowfall"
            elif code >= 95:
                cond = "Thunderstorm"
            return {
                "city": f"{loc.get('name')}, {loc.get('country', '')}".strip(", "),
                "temp_c": round(float(cur.get("temperature", 0))),
                "wind_kmh": cur.get("windspeed", 0),
                "condition": cond,
                "lat": round(float(loc["latitude"]), 2),
                "lon": round(float(loc["longitude"]), 2),
            }
    except Exception:
        return None


def detect_system_action(prompt: str, image_mode_on: bool = False) -> Optional[Dict[str, Any]]:
    p = prompt.strip()
    if image_mode_on or re.match(r"^(generate|draw|paint|create|render)\s+(an?\s+)?(image|picture|photo|illustration|art)\b", p, re.I):
        clean_p = re.sub(r"^(generate|draw|paint|create|render)\s+(an?\s+)?(image|picture|photo|illustration|art)\s*(of|showing)?", "", p, flags=re.I).strip()
        return {"type": "image_gen", "prompt": clean_p or p}

    light_m = re.search(r"(turn|switch|set|dim|brighten|change)?\s*(the\s*)?(lights?|lamps?|rgb|led|chroma)\s*(on|off|up|down|to\s+\d+%?)?", p, re.I)
    if light_m and any(k in p.lower() for k in ("light", "rgb", "led", "chroma", "dim", "brightness")):
        brightness = 80
        if "off" in p.lower():
            brightness = 0
        elif "dim" in p.lower():
            brightness = 25
        elif "max" in p.lower() or "100%" in p.lower():
            brightness = 100
        pct = re.search(r"(\d{1,3})\s*%", p)
        if pct:
            brightness = max(0, min(100, int(pct.group(1))))
        return {"type": "iot_lights", "brightness": brightness}

    w_m = re.search(r"(?:weather|forecast|temperature)\s+(?:in|for|at)\s+([A-Za-z\s]+)", p, re.I)
    if w_m:
        return {"type": "weather", "city": w_m.group(1).strip().rstrip("?!.")}

    t_m = re.search(r"timer\s+(?:for\s+)?(\d+)\s*(s|sec|seconds?|m|min|minutes?|h|hours?)", p, re.I)
    if t_m:
        n = int(t_m.group(1))
        u = t_m.group(2).lower()
        sec = n * (3600 if u.startswith("h") else 60 if u.startswith("m") else 1)
        return {"type": "timer", "seconds": sec, "label": f"{n} {u}"}

    if re.search(r"who\s+(created|made|built|developed|designed|coded)\s+(you|this|genesis)", p, re.I) or "your creator" in p.lower():
        return {"type": "creator"}
    return None


def generate_flux_image(prompt: str, style: str = "Photorealistic", aspect: str = "1:1") -> Tuple[Optional[bytes], str]:
    style_map = {
        "Photorealistic": "photorealistic, 8k raw photography, hyper-detailed, studio lighting",
        "Anime / Manga": "anime aesthetic, clean linework, vibrant makoto shinkai style",
        "Cyberpunk": "cyberpunk style, neon cyan lights, rainy reflections, octane render",
        "Cinematic": "cinematic film still, 35mm anamorphic lighting, ultra detailed",
        "Digital Art": "digital art masterpiece, trending on artstation, concept art",
        "3D Render": "3d octane render, ray tracing, volumetric lighting, 8k",
    }
    dims = {"1:1": (512, 512), "16:9": (768, 432), "9:16": (432, 768), "4:3": (640, 480), "3:4": (480, 640)}
    w, h = dims.get(aspect, (512, 512))
    full_prompt = f"{prompt}, {style_map.get(style, '')}".strip(", ")
    seed = int(time.time() * 1000) % 999999
    url = f"https://image.pollinations.ai/prompt/{quote(full_prompt)}?width={w}&height={h}&seed={seed}&model=flux&nologo=true"
    try:
        with httpx.Client(timeout=45.0, follow_redirects=True) as client:
            r = client.get(url)
            if r.status_code == 200 and len(r.content) > 500:
                return r.content, url
    except Exception:
        pass
    return None, url


def render_timer_widget(seconds: int, label: str) -> None:
    tid = f"t_{uuid.uuid4().hex[:6]}"
    _render_html_component(
        f"""
<div style="background:#0b1426;border:1px solid #fbbf2466;border-radius:12px;padding:14px;color:#e6f1ff;font-family:sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <b style="color:#fbbf24;">⏱ Cybernetic Timer ({html_lib.escape(label)})</b>
    <span id="{tid}_st" style="background:#fbbf24;color:#000;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;">ACTIVE</span>
  </div>
  <div id="{tid}_disp" style="font-size:32px;font-weight:800;font-family:monospace;margin:8px 0;color:#00f0ff;">00:00</div>
  <div style="display:flex;gap:8px;">
    <button onclick="startT()" style="background:#16274a;color:#fbbf24;border:1px solid #fbbf24;border-radius:6px;padding:4px 12px;cursor:pointer;">Restart</button>
    <button onclick="pauseT()" style="background:#16274a;color:#e6f1ff;border:1px solid #38bdf8;border-radius:6px;padding:4px 12px;cursor:pointer;">Pause</button>
  </div>
</div>
<script>
let rem = {seconds}, h = null;
function draw() {{
  const m = String(Math.floor(rem / 60)).padStart(2, '0');
  const s = String(rem % 60).padStart(2, '0');
  document.getElementById('{tid}_disp').textContent = rem <= 0 ? '00:00 - TIME UP!' : m + ':' + s;
}}
function pauseT() {{ if (h) clearInterval(h); h = null; document.getElementById('{tid}_st').textContent = 'PAUSED'; }}
function startT() {{
  pauseT(); rem = {seconds}; document.getElementById('{tid}_st').textContent = 'RUNNING'; draw();
  h = setInterval(() => {{
    rem--; draw();
    if (rem <= 0) {{
      clearInterval(h); h = null;
      document.getElementById('{tid}_st').textContent = 'COMPLETE';
      try {{
        const c = new (window.AudioContext || window.webkitAudioContext)();
        const o = c.createOscillator(); o.frequency.value = 880; o.connect(c.destination);
        o.start(); o.stop(c.currentTime + 0.35);
      }} catch(e) {{}}
    }}
  }}, 1000);
}}
startT();
</script>
""",
        height=135,
    )


def record_telemetry(provider: str, model: str, latency_ms: float, tokens: int, endpoint: str, snippet: str, status: str = "success") -> None:
    st.session_state.session_analytics.insert(
        0,
        {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            "endpoint": endpoint,
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 1),
            "tokens_est": tokens,
            "status": status,
            "snippet": snippet[:55],
        },
    )
    st.session_state.session_analytics = st.session_state.session_analytics[:200]
    try:
        AnalyticsTracker.record_request(
            client_ip="streamlit-session",
            user_agent="Streamlit/GENESIS-5.0",
            endpoint=endpoint,
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            status=status,
            tokens_est=tokens,
            prompt_snippet=snippet,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 6. Core Execution Helpers (Chat, Swarm, Arena)
# ---------------------------------------------------------------------------
async def _collect_stream_async(
    messages: List[Dict[str, Any]],
    model_choice: str,
    profile: Optional[str],
    temperature: float,
    max_tokens: int,
    session_keys: Dict[str, str],
) -> Dict[str, Any]:
    chunks: List[str] = []
    decision: Dict[str, Any] = {}
    used_provider = "pollinations" if IS_STREAMLIT_CLOUD else "smart-router"
    used_model = model_choice
    t0 = time.perf_counter()
    last_q = messages[-1].get("content", "Hello") if messages else "Hello"

    if model_choice.startswith("profile:"):
        prof_key = model_choice.split(":", 1)[1]
        async for ev in SmartRouter.route_and_execute_stream(
            messages=messages,
            profile_override=None if prof_key == "auto" else prof_key,
            temperature=temperature,
            max_tokens=max_tokens,
            session_keys=session_keys,
        ):
            if ev.get("meta_event") == "routing_decision":
                decision = ev
            elif ev.get("delta"):
                chunks.append(ev["delta"])
            if ev.get("provider"):
                used_provider = ev["provider"]
            if ev.get("model"):
                used_model = ev["model"]
    else:
        prov, mod = model_choice.split("/", 1)
        had_err = False
        async for ev in UniversalAdapter.chat_stream(
            provider_id=prov,
            model=mod,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            session_keys=session_keys,
        ):
            if ev.get("error"):
                had_err = True
            if ev.get("delta"):
                chunks.append(ev["delta"])
            if ev.get("provider"):
                used_provider = ev["provider"]
            if ev.get("model"):
                used_model = ev["model"]
        joined_err = "".join(chunks)
        if had_err and (prov == "pollinations" or "Pollinations unavailable" in joined_err or not joined_err.strip()):
            fb_text, fb_prov, fb_mod = await asyncio.to_thread(
                SmartRouter.generate_uninterrupted_fallback_meta, last_q, prov == "pollinations"
            )
            chunks = [fb_text]
            used_provider, used_model = fb_prov, fb_mod
        elif had_err and chunks and "Missing API key" in joined_err:
            chunks.append(
                "\n\n> 💡 *Tip:* Add your API key in **🌐 22 Providers Matrix**, or select **✨ GENESIS 5.0 Auto-Router** above for automatic keyless answers."
            )

    full_text = "".join(chunks).strip()
    if not full_text:
        full_text, fb_prov, fb_mod = await asyncio.to_thread(
            SmartRouter.generate_uninterrupted_fallback_meta, last_q, True
        )
        used_provider, used_model = fb_prov, fb_mod

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    tokens_est = max(1, len(full_text) // 4)
    tok_s = round(tokens_est / max(0.15, latency_ms / 1000.0), 1)
    return {
        "text": full_text,
        "provider": used_provider,
        "model": used_model,
        "latency_ms": latency_ms,
        "tokens": tokens_est,
        "tok_s": tok_s,
        "decision": decision,
    }


async def _run_swarm_async(prompt: str, session_keys: Dict[str, str]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    arch_msgs = [{"role": "user", "content": f"[ARCHITECT AGENT]: Design the core structural architecture and methodology for: {prompt}"}]
    crit_msgs = [{"role": "user", "content": f"[CRITIC AGENT]: Identify edge cases, constraints, security risks, and trade-offs for: {prompt}"}]

    arch_res, crit_res = await asyncio.gather(
        _collect_stream_async(arch_msgs, "profile:coding", "coding", 0.5, 1024, session_keys),
        _collect_stream_async(crit_msgs, "profile:reasoning", "reasoning", 0.4, 1024, session_keys),
    )

    synth_prompt = (
        f"[CHIEF SYNTHESIZER AGENT]: Reconcile both perspectives into an authoritative unified answer.\n\n"
        f"[ARCHITECT]:\n{arch_res['text'][:1200]}\n\n"
        f"[CRITIC]:\n{crit_res['text'][:1200]}\n\n"
        f"Original Question: {prompt}"
    )
    synth_res = await _collect_stream_async(
        [{"role": "user", "content": synth_prompt}], "profile:general", "general", 0.5, 1400, session_keys
    )
    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "architect": arch_res["text"],
        "critic": crit_res["text"],
        "synthesizer": synth_res["text"],
        "latency_ms": total_ms,
        "tokens": arch_res["tokens"] + crit_res["tokens"] + synth_res["tokens"],
    }


async def _run_arena_async(selected: List[Tuple[str, str]], prompt: str, session_keys: Dict[str, str]) -> List[Dict[str, Any]]:
    async def one(idx: int, prov: str, mod: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        parts: List[str] = []
        used_p = prov
        used_m = mod
        had_err = False
        async for chunk in UniversalAdapter.chat_stream(
            provider_id=prov,
            model=mod,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1200,
            session_keys=session_keys,
        ):
            if chunk.get("error"):
                had_err = True
            if chunk.get("delta"):
                parts.append(chunk["delta"])
            if chunk.get("provider"):
                used_p = chunk["provider"]
            if chunk.get("model"):
                used_m = chunk["model"]
        lat = round((time.perf_counter() - t0) * 1000, 1)
        txt = "".join(parts).strip()
        toks = max(1, len(txt) // 4)
        return {
            "slot": idx,
            "requested": f"{prov}/{mod}",
            "actual": f"{used_p}/{used_m}",
            "provider": used_p,
            "model": used_m,
            "text": txt,
            "latency_ms": lat,
            "tok_s": round(toks / max(0.15, lat / 1000.0), 1),
            "words": len(txt.split()),
            "error": had_err,
        }

    return list(await asyncio.gather(*(one(i, p, m) for i, (p, m) in enumerate(selected))))


# ---------------------------------------------------------------------------
# 7. Sidebar & Top Telemetry Header
# ---------------------------------------------------------------------------
def render_sidebar() -> None:
    b64 = _logo_b64()
    with st.sidebar:
        logo_html = (
            f'<img src="data:image/png;base64,{b64}" style="width:42px;height:42px;border-radius:50%;border:2px solid {ACCENT};box-shadow:0 0 14px {GLOW};object-fit:cover;">'
            if b64
            else "⚡"
        )
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;padding:6px 0 12px 0;">
              {logo_html}
              <div>
                <div style="font-weight:900;font-size:17px;letter-spacing:0.08em;color:#fff;">GENESIS AI <span style="color:{ACCENT};">5.0</span></div>
                <div style="font-size:11px;color:#94a3b8;">22 Providers • 64 Models • 2.4" TFT</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("➕ New Chat Session", width="stretch", type="primary"):
            cid = f"chat_{uuid.uuid4().hex[:8]}"
            st.session_state.chats[cid] = {
                "id": cid,
                "title": "New GENESIS Session",
                "messages": [],
                "created_at": time.strftime("%H:%M"),
            }
            st.session_state.current_chat_id = cid
            st.session_state.workspace = "💬 ChatGPT Chat"
            st.rerun()

        st.markdown("##### WORKSPACES")
        workspaces = [
            "💬 ChatGPT Chat",
            "⚔️ 4-Way Arena",
            "🔀 Neural Routing Map",
            "🌐 22 Providers Matrix",
            "🎁 100% Free AI Hub",
            "📊 User Analytics",
            "🔌 API Proxy & SDK",
            "📟 2.4\" Hardware Screen ⚡",
        ]
        st.session_state.workspace = st.radio(
            "Workspace",
            workspaces,
            index=workspaces.index(st.session_state.workspace) if st.session_state.workspace in workspaces else 0,
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("##### RECENT CHATS")
        chat_ids = list(reversed(list(st.session_state.chats.keys())))
        for cid in chat_ids[:10]:
            chat = st.session_state.chats[cid]
            col_a, col_b = st.columns([0.82, 0.18])
            with col_a:
                label = f"{'▶ ' if cid == st.session_state.current_chat_id else ''}{chat['title'][:24]}"
                if st.button(label, key=f"sel_{cid}", width="stretch"):
                    st.session_state.current_chat_id = cid
                    st.session_state.workspace = "💬 ChatGPT Chat"
                    st.rerun()
            with col_b:
                if len(st.session_state.chats) > 1 and st.button("🗑", key=f"del_{cid}"):
                    del st.session_state.chats[cid]
                    if st.session_state.current_chat_id == cid:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()

        st.markdown("---")
        st.markdown("##### THEME & 2.4\" SCREEN SYNC")
        st.session_state.theme_name = st.selectbox(
            "Theme Matrix",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme_name),
        )
        st.session_state.mirror_screen = st.toggle("Auto-Mirror Answers to 2.4\" Screen", value=st.session_state.mirror_screen)
        st.session_state.relay_sync = st.toggle("Cloud Relay Sync (Phone -> ESP32)", value=st.session_state.relay_sync)
        st.caption("Created by **Ishit Jain** • Sovereign AI")


def render_top_hud() -> None:
    total_models = sum(len(v.get("models", [])) for v in PROVIDERS_METADATA.values())
    env_label = "CLOUD STREAMLIT GATEWAY" if IS_STREAMLIT_CLOUD else "LOCAL DUAL-BRAIN GATEWAY"
    keyless_cloud = IS_STREAMLIT_CLOUD and not _has_any_api_key()
    cloud_mode_badge = (
        '<span class="gen-badge" style="border-color:#f59e0b;color:#fcd34d;">Keyless Mode: Pollinations + Wiki/DDG</span>'
        if keyless_cloud
        else ""
    )
    keyless_tip_html = (
        '<div style="margin-top:8px;font-size:11px;color:#cbd5e1;border-top:1px solid rgba(56,189,248,0.16);padding-top:6px;">'
        '🔑 <b>Tip:</b> Running keyless (Pollinations 45s cooldown + Live Knowledge Engine). '
        'Add a free <code>GEMINI_API_KEY</code> or <code>GROQ_API_KEY</code> in <b>🌐 22 Providers Matrix</b> or Streamlit <b>Secrets</b> for unlimited LLM chat.'
        '</div>'
        if keyless_cloud
        else ""
    )
    hero_lines = [
        '<div class="gen-hero">',
        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">',
        '<div>',
        f'<div style="font-size:20px;font-weight:900;color:#fff;letter-spacing:0.04em;">⚡ GENESIS AI 5.0 <span style="color:{ACCENT};font-size:14px;">// {env_label}</span></div>',
        '<div style="font-size:12px;color:#94a3b8;">Smart Intent Router • Live Search & Swarm • Image Studio RGB565 • ESP32-C5 2.4&quot; TFT Bridge</div>',
        '</div>',
        '<div class="gen-pill-row">',
        f'<span class="gen-badge">{len(PROVIDERS_METADATA)} Providers / {total_models} Models</span>',
        f'<span class="gen-badge">Velocity: {st.session_state.last_tok_speed} tok/s</span>',
        f'<span class="gen-badge">Screen Sync: {"ON" if st.session_state.mirror_screen else "OFF"}</span>',
        cloud_mode_badge,
        '</div>',
        '</div>',
        keyless_tip_html,
        '</div>',
    ]
    st.markdown("\n".join(line for line in hero_lines if line), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 8. Workspace 1: ChatGPT Chat
# ---------------------------------------------------------------------------
def _build_model_options() -> Tuple[List[str], Dict[str, str]]:
    options = [
        "profile:auto",
        "profile:reasoning",
        "profile:speed",
        "profile:coding",
        "profile:free_tier",
        "profile:search",
    ]
    labels = {
        "profile:auto": "✨ GENESIS 5.0 Auto-Router (Recommended)",
        "profile:reasoning": "🧠 GENESIS 5.0 Deep Reasoning (R1 / Thinking)",
        "profile:speed": "⚡ GENESIS 5.0 Ultra-Speed (<100ms)",
        "profile:coding": "💻 GENESIS 5.0 Elite Coder",
        "profile:free_tier": "🎁 GENESIS 5.0 100% Free Tier",
        "profile:search": "🌐 GENESIS 5.0 Web Search",
    }
    if not IS_STREAMLIT_CLOUD:
        options.append("profile:local_offline")
        labels["profile:local_offline"] = "🖥️ Local Offline Brain (Ollama llama3.2:1b)"

    for pid, meta in PROVIDERS_METADATA.items():
        if IS_STREAMLIT_CLOUD and pid == "ollama":
            continue
        for m in meta.get("models", []):
            key = f"{pid}/{m['id']}"
            options.append(key)
            free_tag = " [FREE]" if m.get("free") else ""
            labels[key] = f"{meta['name']} — {m['name']}{free_tag}"
    return options, labels


def _render_system_action_card(action: Dict[str, Any], prompt: str) -> Tuple[str, Optional[bytes]]:
    extra_summary = ""
    gen_img_bytes: Optional[bytes] = None
    atype = action["type"]
    if atype == "creator":
        st.markdown(
            """
            <div class="gen-card" style="border-color:#00f0ff88;">
              <b style="color:#00f0ff;">👨‍💻 Created by Ishit Jain — Lead Systems Architect</b><br>
              <span style="font-size:13px;color:#cbd5e1;">GENESIS AI 5.0 unifies 22 AI providers, multi-agent swarm consensus, live web search, and real-time ESP32-C5 2.4" TFT hardware control.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif atype == "iot_lights":
        b = action["brightness"]
        dispatch_screen_command({"action": "rgb", "brightness": b}, force=True)
        st.success(f"💡 GENESIS PHOTON GPIO27 RGB LED command dispatched: Brightness set to **{b}%**.")
    elif atype == "weather":
        w = fetch_weather_hud(action["city"])
        if w:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Location", w["city"])
            c2.metric("Temperature", f"{w['temp_c']} °C")
            c3.metric("Condition", w["condition"])
            c4.metric("Wind", f"{w['wind_kmh']} km/h")
            extra_summary = f"Live Weather in {w['city']}: {w['temp_c']}°C, {w['condition']}, Wind {w['wind_kmh']} km/h."
    elif atype == "timer":
        render_timer_widget(action["seconds"], action["label"])
        extra_summary = f"Timer active for {action['label']}."
    elif atype == "image_gen":
        with st.spinner("🎨 Generating Flux.1 HD Artwork..."):
            img_bytes, img_url = generate_flux_image(action["prompt"], style="Photorealistic", aspect="1:1")
        if img_bytes:
            gen_img_bytes = img_bytes
            st.image(img_bytes, caption=f"Flux.1 Generated: {action['prompt']}", width=380)
            shared = get_shared_screen_state()
            with shared["lock"]:
                shared["last_image_bytes"] = img_bytes
                shared["last_image_url"] = img_url
                shared["last_image_prompt"] = action["prompt"]
            if HAS_PIL and st.session_state.mirror_screen:
                tx, ty, tw, th, chunks = encode_image_rgb565_chunks(img_bytes, "1:1")
                dispatch_screen_command({
                    "action": "tft_image",
                    "prompt": action["prompt"],
                    "style": "Photorealistic",
                    "aspect": "1:1",
                    "x": tx, "y": ty, "w": tw, "h": th, "chunks": chunks,
                })
                st.toast("Image streamed to 2.4\" ESP32 TFT queue!", icon="📟")
            extra_summary = f"Generated Flux.1 HD artwork for: {action['prompt']}."
        else:
            st.info(f"Flux Image URL generated: {img_url}")
    return extra_summary, gen_img_bytes


def _render_hardware_dock_content(tft_slot) -> None:
    shared = get_shared_screen_state()
    tft_slot.markdown(
        _build_tft_bezel_html(shared, st.session_state.esp_ip, compact=True),
        unsafe_allow_html=True,
    )


def render_chat_workspace() -> None:
    current_chat = st.session_state.chats[st.session_state.current_chat_id]
    model_options, model_labels = _build_model_options()

    c_top1, c_top2, c_top3, c_top4, c_top5, c_top6 = st.columns([2.35, 0.9, 0.9, 0.9, 0.9, 1.05])
    with c_top1:
        selected_model = st.selectbox(
            "Active Model / Router",
            model_options,
            format_func=lambda k: model_labels.get(k, k),
            label_visibility="collapsed",
        )
    with c_top2:
        use_search = st.toggle("🌐 Search", value=False)
    with c_top3:
        use_reason = st.toggle("🧠 Reason", value=False)
    with c_top4:
        use_swarm = st.toggle("🤖 Swarm", value=False)
    with c_top5:
        use_image = st.toggle("🎨 Image", value=False)
    with c_top6:
        st.session_state.present_screen_dock = st.toggle(
            "📟 2.4\" Dock",
            value=st.session_state.present_screen_dock,
            help="Show or hide the Live 2.4-inch Hardware Screen Presenter next to chat",
        )

    with st.expander("📎 Attach Image / Document (Vision & Context)  &  🎤 Voice Assistant"):
        up_col, voice_col = st.columns([1.3, 1.0])
        with up_col:
            uploaded_files = st.file_uploader(
                "Upload Image (PNG/JPG) or Code/Text/CSV/JSON/MD",
                type=["png", "jpg", "jpeg", "webp", "txt", "py", "js", "json", "csv", "md"],
                accept_multiple_files=True,
                key="chat_attachments",
            )
        with voice_col:
            _render_html_component(
                """
                <div style="background:#070d1c;border:1px solid #1c3558;border-radius:10px;padding:10px;color:#e6f1ff;font-family:sans-serif;font-size:12px;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <b style="color:#00f0ff;">🎙 Voice Dictation & TTS</b>
                    <button onclick="startMic()" style="background:#00f0ff;color:#02131f;border:0;border-radius:6px;padding:3px 10px;font-weight:700;cursor:pointer;">Speak</button>
                  </div>
                  <div id="micOut" style="color:#94a3b8;min-height:28px;">Tap Speak, then copy dictated text into chat below.</div>
                </div>
                <script>
                function startMic() {
                  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                  const out = document.getElementById('micOut');
                  if (!SR) { out.textContent = 'Web Speech API not supported in this browser.'; return; }
                  const r = new SR(); r.lang = 'en-US';
                  out.textContent = 'Listening...';
                  r.onresult = (e) => {
                    const txt = e.results[0][0].transcript;
                    out.textContent = 'Heard: "' + txt + '" (copied to clipboard)';
                    navigator.clipboard?.writeText(txt).catch(()=>{});
                  };
                  r.onerror = (e) => { out.textContent = 'Mic error: ' + e.error; };
                  r.start();
                }
                </script>
                """,
                height=92,
            )

    tft_slot = None
    if st.session_state.present_screen_dock:
        col_chat, col_tft = st.columns([1.65, 1.05], gap="medium")
        with col_tft:
            st.markdown("##### 📟 Live 2.4\" Screen Presenter")
            tft_slot = st.empty()
            _render_hardware_dock_content(tft_slot)
            d1, d2, d3 = st.columns(3)
            with d1:
                if st.button("⏭ Page", key="dock_page_btn", width="stretch"):
                    dispatch_screen_command({"action": "page"}, force=True)
                    st.toast("Next 2.4\" TFT page triggered!", icon="📟")
            with d2:
                if st.button("🧹 Clear", key="dock_clear_btn", width="stretch"):
                    dispatch_screen_command({"action": "clear"}, force=True)
                    _render_hardware_dock_content(tft_slot)
                    st.toast("2.4\" TFT cleared!", icon="🧹")
            with d3:
                if st.button("🎛 Full Studio", key="dock_full_btn", width="stretch"):
                    st.session_state.workspace = "📟 2.4\" Hardware Screen ⚡"
                    st.rerun()
            if IS_STREAMLIT_CLOUD:
                st.caption(f"🔄 Browser Loopback → `127.0.0.1:8000` • ESP32 Target: `{st.session_state.esp_ip}`")
            else:
                st.caption(f"🟢 Local Hardware Bridge → ESP32 `{st.session_state.esp_ip}` / `192.168.4.1` / `COM4`")
        chat_host = col_chat
    else:
        chat_host = st.container()

    with chat_host:
        starter_slot = st.empty()
        if not current_chat["messages"] and not st.session_state.pending_starter_prompt:
            with starter_slot.container():
                st.markdown("#### What can I help with today?")
                starters = [
                    ("⚛️ Quantum Key Distribution", "Explain quantum key distribution (BB84 protocol) with a complete Python simulation script."),
                    ("🧠 Mathematical Induction Proof", "Prove by mathematical induction that for all n >= 1: 1 + 2 + ... + n = n(n+1)/2."),
                    ("⚡ Transformer vs Mamba", "Compare Transformer attention mechanisms vs Mamba state-space models in 3 crisp points."),
                    ("🌐 2026 AI Agent Breakthroughs", "What are the key architectures used in modern autonomous multi-agent systems?"),
                ]
                s_cols = st.columns(2)
                for i, (title, p_text) in enumerate(starters):
                    if s_cols[i % 2].button(f"{title}\n\n{p_text[:58]}...", key=f"starter_{i}", width="stretch"):
                        st.session_state.pending_starter_prompt = p_text
                        st.rerun()

        msgs_list = current_chat["messages"]
        for idx, msg in enumerate(msgs_list):
            with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else "🧑‍🚀"):
                if msg.get("thought"):
                    with st.expander("🧠 Thinking Process..."):
                        st.markdown(msg["thought"])
                st.markdown(msg["content"])
                if msg.get("citations"):
                    st.markdown("**🔗 Grounded Sources:** " + " • ".join(f"[{c['title']}]({c['url']})" for c in msg["citations"]))
                if msg.get("image_bytes"):
                    st.image(msg["image_bytes"], width=360)
                if msg.get("meta"):
                    st.caption(msg["meta"])
                if msg["role"] == "assistant":
                    if st.button("📟 Present on 2.4\" Screen", key=f"push_msg_{idx}"):
                        dispatch_screen_command(
                            {
                                "action": "feed",
                                "state": "ANSWERED",
                                "question": msg.get("question", current_chat["title"]),
                                "text": msg["content"],
                                "provider": msg.get("provider", "Gemini"),
                                "model": msg.get("model", "GENESIS AI 5.0"),
                            },
                            force=True,
                        )
                        if tft_slot is not None:
                            _render_hardware_dock_content(tft_slot)
                        st.toast("Presented on 2.4\" Screen!", icon="⚡")
                elif idx == len(msgs_list) - 1:
                    if st.button("🔄 Answer This Prompt Now", key=f"retry_orphan_{idx}"):
                        recovered = msgs_list.pop()["content"]
                        st.session_state.pending_starter_prompt = recovered
                        st.rerun()

    user_prompt = st.chat_input("Message GENESIS AI 5.0, or ask for weather, timer, RGB light, image...")
    if not user_prompt and st.session_state.pending_starter_prompt:
        user_prompt = st.session_state.pending_starter_prompt
        st.session_state.pending_starter_prompt = None

    if not user_prompt:
        return

    with chat_host:
        starter_slot.empty()
        if not current_chat["messages"]:
            current_chat["title"] = user_prompt[:30] + ("..." if len(user_prompt) > 30 else "")

        history_snapshot = [
            {"role": m["role"], "content": m["content"]}
            for m in current_chat["messages"][-6:]
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]

        with st.chat_message("user", avatar="🧑‍🚀"):
            st.markdown(user_prompt)

        dispatch_screen_command(
            {"action": "feed", "state": "THINKING", "question": user_prompt, "provider": "SmartRouter", "model": selected_model},
        )
        if tft_slot is not None:
            _render_hardware_dock_content(tft_slot)

        attached_images: List[Dict[str, str]] = []
        attached_text_blocks: List[str] = []
        if uploaded_files:
            for uf in uploaded_files:
                raw = uf.read()
                if uf.type.startswith("image/"):
                    attached_images.append({"mime_type": uf.type, "data": base64.b64encode(raw).decode("ascii")})
                else:
                    decoded = raw.decode("utf-8", errors="replace")[:8000]
                    attached_text_blocks.append(f"[Attached file `{uf.name}`]:\n```\n{decoded}\n```")

        gen_image_bytes: Optional[bytes] = None
        citations: List[Dict[str, str]] = []
        thought_txt = ""
        final_text = ""
        used_prov = "genesis-router"
        used_mod = selected_model
        meta_str = ""

        with st.chat_message("assistant", avatar="⚡"):
            detected_action = detect_system_action(user_prompt, image_mode_on=use_image)
            if detected_action:
                action_context, gen_image_bytes = _render_system_action_card(detected_action, user_prompt)
            else:
                action_context = ""

            search_ctx = ""
            if use_search or selected_model == "profile:search":
                with st.status("🌐 Fetching Live Web Search Grounding...", expanded=False):
                    search_ctx, citations = fetch_live_web_search(user_prompt)

            if use_swarm or user_prompt.lower().startswith("@swarm"):
                with st.spinner("🤖 Running 3-Agent Swarm Consensus (Architect + Critic + Synthesizer)..."):
                    try:
                        swarm = run_async(asyncio.wait_for(_run_swarm_async(user_prompt, st.session_state.user_keys), timeout=45.0))
                        col_a, col_c = st.columns(2)
                        with col_a:
                            st.markdown("**🏛️ Architect Agent**")
                            st.markdown(swarm["architect"])
                        with col_c:
                            st.markdown("**🛡️ Critic Agent**")
                            st.markdown(swarm["critic"])
                        st.markdown("---")
                        st.markdown("**⚡ Chief Synthesizer Unified Consensus**")
                        st.markdown(swarm["synthesizer"])
                        final_text = swarm["synthesizer"]
                        meta_str = f"3-Agent Swarm • {swarm['latency_ms']} ms • {swarm['tokens']} est. tokens"
                        used_prov, used_mod = "swarm", "architect+critic+synth"
                        st.session_state.last_tok_speed = round(swarm["tokens"] / max(0.2, swarm["latency_ms"] / 1000.0), 1)
                        record_telemetry(used_prov, used_mod, swarm["latency_ms"], swarm["tokens"], "streamlit:swarm", user_prompt)
                    except Exception:
                        t_fb = time.perf_counter()
                        final_text, used_prov, used_mod = SmartRouter.generate_uninterrupted_fallback_meta(
                            user_prompt, skip_pollinations=True
                        )
                        lat_fb = round((time.perf_counter() - t_fb) * 1000, 1)
                        toks_fb = max(1, len(final_text) // 4)
                        meta_str = f"Provider: `{used_prov}` • Model: `{used_mod}` • {lat_fb} ms"
                        st.markdown(final_text)
                        st.caption(meta_str)
                        record_telemetry(used_prov, used_mod, lat_fb, toks_fb, "streamlit:swarm-fallback", user_prompt)
            else:
                effective_prompt = user_prompt
                if attached_text_blocks:
                    effective_prompt += "\n\n" + "\n\n".join(attached_text_blocks)
                if action_context:
                    effective_prompt += f"\n\n[Live System Action Context]: {action_context}"
                if search_ctx:
                    effective_prompt += search_ctx

                llm_messages: List[Dict[str, Any]] = [
                    {
                        "role": "system",
                        "content": "You are GENESIS AI 5.0, created by Ishit Jain. Be crisp, accurate, helpful, and authoritative.",
                    }
                ]
                llm_messages.extend(history_snapshot)

                last_msg: Dict[str, Any] = {"role": "user", "content": effective_prompt}
                if attached_images:
                    last_msg["images"] = attached_images
                    if selected_model.startswith("profile:") and get_resolved_key("GEMINI_API_KEY"):
                        selected_model = "gemini/gemini-3.5-flash-lite"
                llm_messages.append(last_msg)

                eff_model = "profile:reasoning" if (use_reason and selected_model == "profile:auto") else selected_model
                with st.spinner("⚡ Synthesizing response via GENESIS Cognitive Router..."):
                    try:
                        res = run_async(
                            asyncio.wait_for(
                                _collect_stream_async(
                                    messages=llm_messages,
                                    model_choice=eff_model,
                                    profile="reasoning" if use_reason else None,
                                    temperature=0.35 if use_reason else 0.7,
                                    max_tokens=2048,
                                    session_keys=st.session_state.user_keys,
                                ),
                                timeout=24.0,
                            )
                        )
                    except Exception:
                        t_fb = time.perf_counter()
                        fb_txt, fb_prov, fb_mod = SmartRouter.generate_uninterrupted_fallback_meta(
                            user_prompt, skip_pollinations=True
                        )
                        lat_fb = round((time.perf_counter() - t_fb) * 1000, 1)
                        toks_fb = max(1, len(fb_txt) // 4)
                        res = {
                            "text": fb_txt,
                            "provider": fb_prov,
                            "model": fb_mod,
                            "latency_ms": lat_fb,
                            "tokens": toks_fb,
                            "tok_s": round(toks_fb / max(0.15, lat_fb / 1000.0), 1),
                            "decision": {},
                        }

                raw_out = res["text"]
                if not raw_out or raw_out.startswith("GENESIS AI: Processed request for"):
                    fb_txt, fb_prov, fb_mod = SmartRouter.generate_uninterrupted_fallback_meta(
                        user_prompt, skip_pollinations=True
                    )
                    raw_out = fb_txt
                    res["provider"] = fb_prov
                    res["model"] = fb_mod
                    res["tokens"] = max(1, len(fb_txt) // 4)
                    res["tok_s"] = round(res["tokens"] / max(0.15, res["latency_ms"] / 1000.0), 1)
                thought_match = re.search(r"<thought>([\s\S]*?)</thought>", raw_out, flags=re.IGNORECASE)
                thought_txt = thought_match.group(1).strip() if thought_match else ""
                final_text = re.sub(r"<thought>[\s\S]*?</thought>", "", raw_out, flags=re.IGNORECASE).strip()

                if thought_txt:
                    with st.expander("🧠 Thinking Process..."):
                        st.markdown(thought_txt)
                st.markdown(final_text)

                if citations:
                    st.markdown("**🔗 Grounded Sources:** " + " • ".join(f"[{c['title']}]({c['url']})" for c in citations))

                meta_str = f"Provider: `{res['provider']}` • Model: `{res['model']}` • {res['latency_ms']} ms • {res['tok_s']} tok/s"
                st.caption(meta_str)
                used_prov, used_mod = res["provider"], res["model"]
                st.session_state.last_tok_speed = res["tok_s"]
                record_telemetry(used_prov, used_mod, res["latency_ms"], res["tokens"], "streamlit:chat", user_prompt)

    current_chat["messages"].extend(
        [
            {"role": "user", "content": user_prompt},
            {
                "role": "assistant",
                "content": final_text,
                "thought": thought_txt,
                "citations": citations,
                "image_bytes": gen_image_bytes,
                "question": user_prompt,
                "provider": used_prov,
                "model": used_mod,
                "meta": meta_str,
            },
        ]
    )

    if not (detected_action and detected_action.get("type") == "image_gen" and gen_image_bytes is not None):
        dispatch_screen_command(
            {
                "action": "feed",
                "state": "ANSWERED",
                "question": user_prompt,
                "text": final_text,
                "provider": used_prov,
                "model": used_mod,
            }
        )
    if tft_slot is not None:
        _render_hardware_dock_content(tft_slot)


# ---------------------------------------------------------------------------
# 9. Workspace 2: 4-Way Arena Colosseum
# ---------------------------------------------------------------------------
def render_arena_workspace() -> None:
    st.markdown("### ⚔️ 4-Way Model Arena Colosseum")
    st.caption("Broadcast a single prompt to 4 models simultaneously in parallel and compare latency, tok/s, and reasoning quality.")

    all_pairs: List[Tuple[str, str, str]] = []
    for pid, meta in PROVIDERS_METADATA.items():
        if IS_STREAMLIT_CLOUD and pid == "ollama":
            continue
        for m in meta.get("models", []):
            all_pairs.append((pid, m["id"], f"{meta['name']} / {m['name']}"))

    key_list = [f"{p}/{m}" for p, m, _ in all_pairs]
    label_map = {f"{p}/{m}": lbl for p, m, lbl in all_pairs}
    defaults = [
        "gemini/gemini-3.5-flash-lite",
        "pollinations/openai",
        "openrouter/openrouter/free",
        "pollinations/deepseek",
    ]

    cols = st.columns(4)
    chosen: List[Tuple[str, str]] = []
    names = ["Model Alpha", "Model Beta", "Model Gamma", "Model Delta"]
    for i, col in enumerate(cols):
        with col:
            def_idx = key_list.index(defaults[i]) if defaults[i] in key_list else min(i, len(key_list) - 1)
            picked = st.selectbox(names[i], key_list, index=def_idx, format_func=lambda x: label_map.get(x, x), key=f"arena_sel_{i}")
            chosen.append(tuple(picked.split("/", 1)))  # type: ignore

    arena_prompt = st.text_input("Arena Battle Prompt", value="Explain how CRISPR gene editing works in 4 crisp bullet points.")
    if st.button("🚀 Launch 4-Way Parallel Duel", type="primary"):
        if not arena_prompt.strip():
            st.warning("Enter a prompt first.")
            return
        with st.spinner("⚔️ Executing 4-way async broadcast..."):
            res_list = run_async(_run_arena_async(chosen, arena_prompt.strip(), st.session_state.user_keys))
        st.session_state.arena_results = res_list
        for r in res_list:
            record_telemetry(r["provider"], r["model"], r["latency_ms"], max(1, len(r["text"]) // 4), "streamlit:arena", arena_prompt)
        if res_list:
            fastest = min(res_list, key=lambda x: x["latency_ms"] if not x["error"] else 999999)
            dispatch_screen_command(
                {
                    "action": "feed",
                    "state": "ANSWERED",
                    "question": arena_prompt,
                    "text": fastest["text"],
                    "provider": fastest["provider"],
                    "model": fastest["model"],
                }
            )

    if st.session_state.arena_results:
        r_cols = st.columns(2)
        for idx, res in enumerate(st.session_state.arena_results):
            with r_cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"**{names[idx]}**: `{res['actual']}`")
                    st.caption(f"Latency: **{res['latency_ms']} ms** • Speed: **{res['tok_s']} tok/s** • Words: **{res['words']}**")
                    st.markdown(res["text"] or "_No output returned._")
                    if st.button("📟 Send This Winner to 2.4\" Screen", key=f"arena_push_{idx}"):
                        dispatch_screen_command(
                            {
                                "action": "feed",
                                "state": "ANSWERED",
                                "question": arena_prompt,
                                "text": res["text"],
                                "provider": res["provider"],
                                "model": res["model"],
                            },
                            force=True,
                        )
                        st.toast("Pushed to 2.4\" Screen!", icon="⚡")


# ---------------------------------------------------------------------------
# 10. Workspace 3: Neural Routing Map
# ---------------------------------------------------------------------------
def render_routing_map_workspace() -> None:
    st.markdown("### 🔀 GENESIS Autonomous Routing Architecture")
    test_prompt = st.text_input(
        "Simulate Live Intent Classification on Any Prompt",
        value="Write a Python binary search algorithm and prove O(log n) time complexity",
    )
    prof_key, confidence, rationale = SmartRouter.classify_intent(test_prompt or "Hello")
    if IS_STREAMLIT_CLOUD and prof_key == "local_offline":
        prof_key = "general"
    profile_meta = SmartRouter.ROUTING_PROFILES.get(prof_key, SmartRouter.ROUTING_PROFILES["general"])
    chain_str = " ➔ ".join(f"{PROVIDERS_METADATA.get(p, {}).get('name', p)} ({m})" for p, m in profile_meta["chain"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted Profile", profile_meta["name"])
    c2.metric("Classifier Confidence", f"{int(confidence * 100)}%")
    c3.metric("Cloud Mode", "Cloud Active" if IS_STREAMLIT_CLOUD else ("Online Dual-Brain" if SmartRouter.check_internet() else "Offline Ollama"))
    st.info(f"**Rationale:** {rationale}\n\n**Fallback Waterfall Chain:** {chain_str}")

    highlight = {
        "speed": "#00f0ff",
        "reasoning": "#8b5cf6",
        "coding": "#10b981",
        "free_tier": "#f59e0b",
        "search": "#ec4899",
    }
    svg_lines = [
        '<div style="background:#050b18;border:1px solid #1c3558;border-radius:14px;padding:12px;">',
        '<svg viewBox="0 0 1100 420" width="100%" height="340">',
        '<line x1="170" y1="210" x2="310" y2="210" stroke="#00f0ff" stroke-width="3"/>',
        f'<line x1="470" y1="210" x2="620" y2="60" stroke="{highlight.get("speed","#334155")}" stroke-width="{4 if prof_key=="speed" else 1.5}"/>',
        f'<line x1="470" y1="210" x2="620" y2="135" stroke="{highlight.get("reasoning","#334155")}" stroke-width="{4 if prof_key=="reasoning" else 1.5}"/>',
        f'<line x1="470" y1="210" x2="620" y2="210" stroke="{highlight.get("coding","#334155")}" stroke-width="{4 if prof_key=="coding" else 1.5}"/>',
        f'<line x1="470" y1="210" x2="620" y2="285" stroke="{highlight.get("free_tier","#334155")}" stroke-width="{4 if prof_key=="free_tier" else 1.5}"/>',
        f'<line x1="470" y1="210" x2="620" y2="360" stroke="{highlight.get("search","#334155")}" stroke-width="{4 if prof_key=="search" else 1.5}"/>',
        '<line x1="820" y1="60" x2="920" y2="210" stroke="#38bdf8" stroke-width="1.5"/>',
        '<line x1="820" y1="135" x2="920" y2="210" stroke="#38bdf8" stroke-width="1.5"/>',
        '<line x1="820" y1="210" x2="920" y2="210" stroke="#38bdf8" stroke-width="2"/>',
        '<line x1="820" y1="285" x2="920" y2="210" stroke="#38bdf8" stroke-width="1.5"/>',
        '<line x1="820" y1="360" x2="920" y2="210" stroke="#38bdf8" stroke-width="1.5"/>',
        '<rect x="30" y="160" width="140" height="100" rx="14" fill="#0d1424" stroke="#00f0ff" stroke-width="2"/>',
        '<text x="100" y="205" text-anchor="middle" fill="#00f0ff" font-size="14" font-weight="700">USER INPUT</text>',
        '<text x="100" y="226" text-anchor="middle" fill="#94a3b8" font-size="11">Text / Vision / Voice</text>',
        '<rect x="310" y="150" width="160" height="120" rx="14" fill="#11192e" stroke="#8b5cf6" stroke-width="2"/>',
        '<text x="390" y="202" text-anchor="middle" fill="#c4b5fd" font-size="13" font-weight="700">INTENT CLASSIFIER</text>',
        f'<text x="390" y="224" text-anchor="middle" fill="#10b981" font-size="12">Active: {prof_key.upper()}</text>',
        f'<rect x="620" y="30" width="200" height="54" rx="10" fill="#0d1b2a" stroke="#00f0ff" stroke-width="{3 if prof_key=="speed" else 1}"/>',
        '<text x="720" y="62" text-anchor="middle" fill="#00f0ff" font-size="13" font-weight="700">⚡ ULTRA-SPEED TIER</text>',
        f'<rect x="620" y="105" width="200" height="54" rx="10" fill="#0d1b2a" stroke="#8b5cf6" stroke-width="{3 if prof_key=="reasoning" else 1}"/>',
        '<text x="720" y="137" text-anchor="middle" fill="#c4b5fd" font-size="13" font-weight="700">🧠 DEEP REASONING</text>',
        f'<rect x="620" y="180" width="200" height="54" rx="10" fill="#0d1b2a" stroke="#10b981" stroke-width="{3 if prof_key=="coding" else 1}"/>',
        '<text x="720" y="212" text-anchor="middle" fill="#6ee7b7" font-size="13" font-weight="700">💻 ELITE CODE TIER</text>',
        f'<rect x="620" y="255" width="200" height="54" rx="10" fill="#0d1b2a" stroke="#f59e0b" stroke-width="{3 if prof_key=="free_tier" else 1}"/>',
        '<text x="720" y="287" text-anchor="middle" fill="#fcd34d" font-size="13" font-weight="700">🆓 ZERO-COST FREE</text>',
        f'<rect x="620" y="330" width="200" height="54" rx="10" fill="#0d1b2a" stroke="#ec4899" stroke-width="{3 if prof_key=="search" else 1}"/>',
        '<text x="720" y="362" text-anchor="middle" fill="#f472b6" font-size="13" font-weight="700">🌐 GROUNDED SEARCH</text>',
        '<rect x="920" y="135" width="150" height="150" rx="14" fill="#131c31" stroke="#00f0ff" stroke-width="2"/>',
        '<text x="995" y="185" text-anchor="middle" fill="#00f0ff" font-size="13" font-weight="700">FALLBACK MATRIX</text>',
        '<text x="995" y="212" text-anchor="middle" fill="#10b981" font-size="11">Auto Retry + Keyless</text>',
        '<text x="995" y="236" text-anchor="middle" fill="#94a3b8" font-size="11">100% Uptime Sync</text>',
        '</svg>',
        '</div>',
    ]
    st.markdown("\n".join(svg_lines), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 11. Workspace 4: 22 Providers Matrix & Session Key Pool
# ---------------------------------------------------------------------------
def render_providers_workspace() -> None:
    st.markdown("### 🌐 Master 22 Providers Matrix & Session Key Pool")
    st.caption(
        "Keys entered here are stored strictly inside your private browser session (`st.session_state`) and are never exposed or shared."
    )

    if st.button("📡 Batch Ping Active Cloud Providers", type="primary"):
        targets = [
            pid
            for pid, meta in PROVIDERS_METADATA.items()
            if (pid != "ollama" or not IS_STREAMLIT_CLOUD) and (pid == "pollinations" or pid == "ollama" or get_resolved_key(meta.get("env_var")))
        ]
        if not targets:
            targets = ["pollinations"]

        async def _batch():
            return await asyncio.gather(
                *(UniversalAdapter.test_ping(pid, api_key_override=st.session_state.user_keys.get(PROVIDERS_METADATA[pid].get("env_var") or "")) for pid in targets)
            )

        with st.spinner(f"Pinging {len(targets)} providers concurrently..."):
            results = run_async(_batch())
        for r in results:
            st.session_state.ping_results[r["provider"]] = r

    cols = st.columns(2)
    for idx, (pid, meta) in enumerate(PROVIDERS_METADATA.items()):
        env_var = meta.get("env_var")
        host_has_key = bool(env_var and GatewayConfig.get_key(env_var))
        sess_key = (st.session_state.user_keys.get(env_var) or "") if env_var else ""
        if pid == "pollinations":
            key_badge = "Keyless Free Cloud"
        elif pid == "ollama":
            key_badge = "Cloud Disabled" if IS_STREAMLIT_CLOUD else "Local Engine"
        elif sess_key:
            key_badge = "Session Key Active"
        elif host_has_key:
            key_badge = "Host Secret Configured (Masked)"
        else:
            key_badge = "Key Needed / Bridges via Router"

        ping_info = st.session_state.ping_results.get(pid)
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{meta['name']}** (`{pid}`) — *{meta['category']}*")
                st.caption(f"Status: `{key_badge}` • Models: **{len(meta.get('models', []))}** • [Get Key]({meta.get('free_key_url', '#')})")
                models_preview = ", ".join(m["id"] for m in meta.get("models", [])[:4])
                st.code(models_preview, language=None)
                if env_var and pid != "ollama":
                    new_k = st.text_input(
                        f"Session {env_var}",
                        value=sess_key,
                        type="password",
                        key=f"key_in_{pid}",
                        placeholder="Optional per-session API key override...",
                    )
                    if new_k != sess_key:
                        st.session_state.user_keys[env_var] = new_k.strip()

                p_c1, p_c2 = st.columns([0.35, 0.65])
                with p_c1:
                    if st.button("Ping", key=f"ping_{pid}"):
                        with st.spinner("Testing..."):
                            st.session_state.ping_results[pid] = run_async(
                                UniversalAdapter.test_ping(pid, api_key_override=sess_key or None)
                            )
                        st.rerun()
                with p_c2:
                    if ping_info:
                        st.caption(f"**{ping_info.get('status')}** ({ping_info.get('latency_ms', 0)} ms) — {ping_info.get('message', '')}")


# ---------------------------------------------------------------------------
# 12. Workspace 5: 100% Free AI Hub
# ---------------------------------------------------------------------------
def render_free_hub_workspace() -> None:
    st.markdown("### 🎁 Verified 100% Free AI Hub")
    st.caption("Zero-cost frontier models and free API developer tiers — no credit card required.")
    free_providers = [m for m in PROVIDERS_METADATA.values() if m.get("free_tier_available")]
    cols = st.columns(2)
    for i, meta in enumerate(free_providers):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{meta['name']}**")
                st.write(meta.get("free_tier_note", ""))
                free_models = [f"`{m['id']}` ({m.get('speed', 'Fast')})" for m in meta.get("models", []) if m.get("free", True)]
                if free_models:
                    st.markdown(" • ".join(free_models))
                st.markdown(f"[🔗 Open Free Key / Portal]({meta.get('free_key_url', '#')}) &nbsp;|&nbsp; [📖 Docs]({meta.get('doc_url', '#')})")


# ---------------------------------------------------------------------------
# 13. Workspace 6: User Analytics & Telemetry
# ---------------------------------------------------------------------------
def render_analytics_workspace() -> None:
    st.markdown("### 📊 Real-Time User Telemetry & Request Analytics")
    server_summary = AnalyticsTracker.get_summary()
    sess_rows = st.session_state.session_analytics
    all_rows = sess_rows if sess_rows else server_summary.get("recent_activity", [])

    df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(
        columns=["timestamp", "endpoint", "provider", "model", "latency_ms", "tokens_est", "status", "snippet"]
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Session Calls", len(sess_rows))
    k2.metric("Total Process Calls", max(len(sess_rows), server_summary.get("total_requests", 0)))
    avg_lat = round(float(df["latency_ms"].mean()), 1) if not df.empty else 0.0
    k3.metric("Avg Latency", f"{avg_lat} ms")
    k4.metric("Est. Tokens", int(df["tokens_est"].sum()) if not df.empty and "tokens_est" in df else 0)

    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            prov_counts = df["provider"].value_counts().reset_index()
            prov_counts.columns = ["provider", "count"]
            if HAS_PLOTLY:
                fig = px.pie(prov_counts, names="provider", values="count", title="Requests by Provider", hole=0.45)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e6f1ff")
                st.plotly_chart(fig, width="stretch")
            else:
                st.bar_chart(prov_counts.set_index("provider"))
        with c2:
            lat_df = df.groupby("model", as_index=False)["latency_ms"].mean()
            if HAS_PLOTLY:
                fig2 = px.bar(lat_df, x="model", y="latency_ms", title="Average Latency (ms) by Model")
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e6f1ff")
                st.plotly_chart(fig2, width="stretch")
            else:
                st.bar_chart(lat_df.set_index("model"))

        st.dataframe(df, width="stretch")
        st.download_button("⬇ Export Telemetry CSV", df.to_csv(index=False).encode("utf-8"), "genesis_telemetry.csv", "text/csv")
    else:
        st.info("No queries logged yet in this session. Send a chat or Arena prompt to populate telemetry!")

    if st.button("🗑 Clear Session Telemetry"):
        st.session_state.session_analytics = []
        st.rerun()


# ---------------------------------------------------------------------------
# 14. Workspace 7: API Proxy & SDK Guide
# ---------------------------------------------------------------------------
def render_proxy_sdk_workspace() -> None:
    st.markdown("### 🔌 GENESIS AI 5.0 API Proxy & SDK Guide")
    endpoint_mode = st.radio(
        "Target OpenAI-Compatible Base URL",
        ["Vercel Cloud (https://omni-model-ai-gateway.vercel.app/v1)", "Local Laptop Gateway (http://localhost:8000/v1)"],
        horizontal=True,
    )
    base_v1 = "https://omni-model-ai-gateway.vercel.app/v1" if "Vercel" in endpoint_mode else "http://localhost:8000/v1"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. Antigravity Python Bridge (`GenesisAI` / `OmniAI`)**")
        st.code(
            """from antigravity_bridge import GenesisAI

genesis = GenesisAI()
print(genesis.chat("Explain quantum key distribution concisely."))
print(genesis.chat("Write binary search in Python", profile="free_tier"))
""",
            language="python",
        )
        st.markdown("**3. Node.js / JavaScript OpenAI SDK**")
        st.code(
            f"""import OpenAI from "openai";
const openai = new OpenAI({{ baseURL: "{base_v1}", apiKey: "genesis-ai" }});
const res = await openai.chat.completions.create({{
  model: "genesis-ai-5.0",
  messages: [{{ role: "user", content: "Hello GENESIS AI 5.0!" }}],
}});
console.log(res.choices[0].message.content);
""",
            language="javascript",
        )
    with c2:
        st.markdown("**2. Standard OpenAI Python SDK**")
        st.code(
            f"""from openai import OpenAI

client = OpenAI(base_url="{base_v1}", api_key="genesis-ai")
res = client.chat.completions.create(
    model="genesis-5.0-speed",
    messages=[{{"role": "user", "content": "Say GENESIS READY"}}],
)
print(res.choices[0].message.content)
""",
            language="python",
        )
        st.markdown("**4. cURL Command**")
        st.code(
            f"""curl {base_v1}/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"genesis-ai-5.0","messages":[{{"role":"user","content":"Hello!"}}],"stream":false}}'
""",
            language="bash",
        )


# ---------------------------------------------------------------------------
# 15. Workspace 8: 2.4" Hardware Screen Simulator & Live ESP32-C5 Controller
# ---------------------------------------------------------------------------
def render_hardware_screen_workspace() -> None:
    shared = get_shared_screen_state()
    st.markdown("### 📟 GENESIS AI 5.0 — 2.4\" Hardware Screen Simulator & ESP32-C5 Live Bridge")

    # Connection configuration card
    with st.expander("⚙️ Hardware Communication Channels (Wi-Fi ESP32-C5 + Loopback + Worldwide Cloud Relay)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.esp_ip = st.text_input("ESP32-C5 Wi-Fi / SoftAP IP", value=st.session_state.esp_ip, help="Example: 10.33.110.73 on hotspot or 192.168.4.1 on GENESIS_AI SoftAP")
            st.session_state.direct_browser_esp = st.checkbox("Try Direct Browser->ESP32 HTTP Push", value=st.session_state.direct_browser_esp, help="Requires HTTP or Private Network Access allowed on your browser")
        with c2:
            st.session_state.local_gateway_url = st.text_input("Local Gateway Loopback URL", value=st.session_state.local_gateway_url, help="Local OmniModelGateway server (http://127.0.0.1:8000)")
        with c3:
            st.session_state.cloud_relay_url = st.text_input("Worldwide Cloud Relay URL", value=st.session_state.cloud_relay_url, help="Used when operating remotely from phone -> home PC sync")

        if IS_STREAMLIT_CLOUD:
            st.info(
                "📡 **Streamlit Cloud -> 2.4\" Screen Architecture:**\n"
                "- **When using Laptop**: Browser Loopback automatically relays commands to local `http://127.0.0.1:8000` (`server.py`), which drives your ESP32 over Wi-Fi/USB.\n"
                "- **When using Phone Anywhere**: Commands push to your Cloud Relay (`omni-model-ai-gateway.vercel.app`), and your laptop running `server.py` or `python cloud_to_esp32_sync.py` forwards them to the ESP32 on wall charger!"
            )
        else:
            st.success("🟢 **Running Locally**: Python `HardwareScreenBridge` talks directly to your ESP32-C5 over Wi-Fi LAN (`" + st.session_state.esp_ip + "`, `192.168.4.1`) and USB `COM4`!")

    # Live Hardware Probe & Simulator Visual
    left_sim, right_ctrl = st.columns([1.15, 1.0])

    with shared["lock"]:
        cur_rgb = shared["rgb_brightness"]
        sync_logs = list(shared["sync_log"])

    with left_sim:
        st.markdown(_build_tft_bezel_html(shared, st.session_state.esp_ip, compact=False), unsafe_allow_html=True)

    with right_ctrl:
        st.markdown("#### 🎮 Tactile Screen & RGB Controls")
        quick_q = st.text_input("Send AI Question Straight to 2.4\" Screen", value="Explain black holes in 20 words")
        if st.button("🚀 Query AI & Stream to 2.4\" Screen", type="primary", width="stretch"):
            dispatch_screen_command({"action": "feed", "state": "THINKING", "question": quick_q, "provider": "Gemini", "model": "GENESIS 5.0"}, force=True)
            with st.spinner("Generating concise 2.4\" TFT response..."):
                try:
                    res = run_async(
                        asyncio.wait_for(
                            _collect_stream_async(
                                messages=[
                                    {"role": "system", "content": "Answer concisely in under 55 plain ASCII words for a 320x240 TFT display."},
                                    {"role": "user", "content": quick_q},
                                ],
                                model_choice="profile:speed",
                                profile="speed",
                                temperature=0.5,
                                max_tokens=200,
                                session_keys=st.session_state.user_keys,
                            ),
                            timeout=20.0,
                        )
                    )
                except Exception:
                    fb_txt, fb_prov, fb_mod = SmartRouter.generate_uninterrupted_fallback_meta(
                        quick_q, skip_pollinations=True
                    )
                    res = {"text": fb_txt, "provider": fb_prov, "model": fb_mod}
            dispatch_screen_command(
                {"action": "feed", "state": "ANSWERED", "question": quick_q, "text": res["text"], "provider": res["provider"], "model": res["model"]},
                force=True,
            )
            st.rerun()

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("⏭ Page", width="stretch"):
                dispatch_screen_command({"action": "page"}, force=True)
                st.toast("Next TFT page triggered!")
        with b2:
            if st.button("🧹 Clear", width="stretch"):
                dispatch_screen_command({"action": "clear"}, force=True)
                st.rerun()
        with b3:
            if st.button("⚛️ Core", width="stretch"):
                with shared["lock"]:
                    shared["fusion_watermark"] = not shared["fusion_watermark"]
                st.rerun()
        with b4:
            if st.button("🔍 Probe", width="stretch"):
                if IS_STREAMLIT_CLOUD:
                    st.info("Cloud cannot directly scan your private LAN; check your local `server.py` / `cloud_to_esp32_sync.py`.")
                else:
                    hardware_bridge.set_target_ip(st.session_state.esp_ip)
                    hw_info = hardware_bridge.query_esp32_status(st.session_state.esp_ip)
                    st.json(hw_info)

        st.markdown("##### 🌈 GENESIS PHOTON Gaming Chroma LED (GPIO 27)")
        rgb_slider = st.slider("Brightness (%)", 0, 100, int(cur_rgb), step=5)
        if st.button("✨ Apply GPIO27 RGB Brightness", width="stretch"):
            dispatch_screen_command({"action": "rgb", "brightness": rgb_slider}, force=True)
            st.toast(f"GENESIS PHOTON GPIO27 brightness set to {rgb_slider}%!")
            st.rerun()

        st.markdown("##### 🖼️ Image Studio -> 2.4\" TFT RGB565 Streamer")
        img_tab1, img_tab2 = st.tabs(["Generate Flux Art", "Upload Image to TFT"])
        with img_tab1:
            art_prompt = st.text_input("Flux Art Prompt", value="Neon cybernetic quantum owl")
            art_style = st.selectbox("Art Style", ["Photorealistic", "Cyberpunk", "Anime / Manga", "Cinematic", "Digital Art", "3D Render"])
            art_aspect = st.selectbox("TFT Aspect Ratio", ["1:1", "16:9", "4:3", "9:16", "3:4"])
            if st.button("🎨 Generate & Stream to 2.4\" TFT", width="stretch"):
                with st.spinner("Generating & encoding RGB565 packets..."):
                    img_bytes, img_url = generate_flux_image(art_prompt, art_style, art_aspect)
                if img_bytes and HAS_PIL:
                    tx, ty, tw, th, chunks = encode_image_rgb565_chunks(img_bytes, art_aspect)
                    with shared["lock"]:
                        shared["last_image_bytes"] = img_bytes
                        shared["last_image_url"] = img_url
                        shared["last_image_prompt"] = art_prompt
                    dispatch_screen_command({
                        "action": "tft_image",
                        "prompt": art_prompt,
                        "style": art_style,
                        "aspect": art_aspect,
                        "x": tx, "y": ty, "w": tw, "h": th, "chunks": chunks,
                    }, force=True)
                    st.success(f"Encoded {len(chunks)} RGB565 packets ({tw}x{th}) -> queued & pushed to ESP32 TFT!")
                    st.rerun()
                else:
                    st.warning("Could not fetch Flux artwork right now; try Upload tab or retry.")

        with img_tab2:
            up_tft = st.file_uploader("Upload PNG/JPG for 2.4\" Display", type=["png", "jpg", "jpeg"], key="tft_img_upload")
            if up_tft and HAS_PIL and st.button("📺 Push Uploaded Image to TFT"):
                raw_b = up_tft.read()
                tx, ty, tw, th, chunks = encode_image_rgb565_chunks(raw_b, "4:3")
                with shared["lock"]:
                    shared["last_image_bytes"] = raw_b
                    shared["last_image_prompt"] = up_tft.name
                dispatch_screen_command({
                    "action": "tft_image",
                    "prompt": up_tft.name,
                    "style": "Upload",
                    "aspect": "4:3",
                    "x": tx, "y": ty, "w": tw, "h": th, "chunks": chunks,
                }, force=True)
                st.success(f"Sent {len(chunks)} RGB565 slices to 2.4\" TFT!")
                st.rerun()

    if sync_logs:
        with st.expander("📡 Live 2.4\" Screen Sync Log"):
            st.code("\n".join(sync_logs), language=None)


# ---------------------------------------------------------------------------
# 16. Main App Dispatch & JS Bridge Flush
# ---------------------------------------------------------------------------
render_sidebar()
render_top_hud()

ws = st.session_state.workspace
if ws == "💬 ChatGPT Chat":
    render_chat_workspace()
elif ws == "⚔️ 4-Way Arena":
    render_arena_workspace()
elif ws == "🔀 Neural Routing Map":
    render_routing_map_workspace()
elif ws == "🌐 22 Providers Matrix":
    render_providers_workspace()
elif ws == "🎁 100% Free AI Hub":
    render_free_hub_workspace()
elif ws == "📊 User Analytics":
    render_analytics_workspace()
elif ws == "🔌 API Proxy & SDK":
    render_proxy_sdk_workspace()
elif ws == "📟 2.4\" Hardware Screen ⚡":
    render_hardware_screen_workspace()

flush_browser_js_bridge()
