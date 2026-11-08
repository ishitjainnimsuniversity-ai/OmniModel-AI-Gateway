"""Runtime settings for GENESIS AI. Secrets are read from the backend .env only."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

# Provider id -> (env var holding the key, OpenAI-compatible base URL or None for native)
PROVIDER_SPECS: Dict[str, Dict[str, Optional[str]]] = {
    "gemini": {"env": "GEMINI_API_KEY", "base": "https://generativelanguage.googleapis.com/v1beta"},
    "openai": {"env": "OPENAI_API_KEY", "base": "https://api.openai.com/v1"},
    "openrouter": {"env": "OPENROUTER_API_KEY", "base": "https://openrouter.ai/api/v1"},
    "groq": {"env": "GROQ_API_KEY", "base": "https://api.groq.com/openai/v1"},
    "deepseek": {"env": "DEEPSEEK_API_KEY", "base": "https://api.deepseek.com"},
    "ollama": {"env": None, "base": "http://127.0.0.1:11434"},
}

DEFAULT_MODELS: Dict[str, str] = {
    "gemini": "gemini-3.5-flash",
    "openai": "gpt-4o-mini",
    "openrouter": "openrouter/free",
    "groq": "llama-3.3-70b-versatile",
    "deepseek": "deepseek-chat",
    "ollama": "llama3.2:1b",
}


DEFAULT_MODEL_FALLBACKS: Dict[str, str] = {
    "gemini": "gemini-3.5-flash-lite",
    "ollama": "",
}


def reload_env() -> None:
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)


def get_secret(env_name: str) -> Optional[str]:
    reload_env()
    val = (os.getenv(env_name) or "").strip().strip("'\"")
    return val or None


def _csv(name: str, default: str = "") -> List[str]:
    reload_env()
    return [x.strip().lower() for x in os.getenv(name, default).split(",") if x.strip()]


class Settings:
    """Live view of configuration (re-read on every access so .env edits apply)."""

    @property
    def mode_preference(self) -> str:
        """Operating mode: 'auto' (preferred), 'cloud' (cloud only), or 'local' (offline first)."""
        reload_env()
        return os.getenv("GENESIS_MODE", "auto").strip().lower()

    @property
    def ollama_base_url(self) -> str:
        reload_env()
        return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")

    @property
    def local_model(self) -> str:
        reload_env()
        return os.getenv("GENESIS_LOCAL_MODEL", "llama3.2:1b").strip()

    def set_local_model(self, model_name: str) -> bool:
        model_name = model_name.strip()
        os.environ["GENESIS_LOCAL_MODEL"] = model_name
        try:
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "GENESIS_LOCAL_MODEL", model_name)
        except Exception:
            pass
        return True

    def set_mode_preference(self, mode: str) -> bool:
        mode = mode.strip().lower()
        if mode not in ("auto", "cloud", "local"):
            return False
        os.environ["GENESIS_MODE"] = mode
        try:
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "GENESIS_MODE", mode)
        except Exception:
            pass
        return True

    @property
    def primary_provider(self) -> str:
        reload_env()
        return os.getenv("GENESIS_PROVIDER", "gemini").strip().lower()

    @property
    def fallback_providers(self) -> List[str]:
        # Fallback happens ONLY for providers listed here AND having a key.
        return [p for p in _csv("GENESIS_FALLBACKS", "") if p != self.primary_provider]

    def model_for(self, provider: str) -> str:
        reload_env()
        if provider == "ollama":
            return self.local_model
        key = f"GENESIS_{provider.upper()}_MODEL"
        if provider == self.primary_provider and os.getenv("GENESIS_MODEL"):
            return os.getenv("GENESIS_MODEL", "").strip()
        return (os.getenv(key) or DEFAULT_MODELS.get(provider, "")).strip()

    def models_for(self, provider: str) -> List[str]:
        """Primary model first, then explicit same-provider fallback models (tried on 429/503/404)."""
        reload_env()
        env = os.getenv(f"GENESIS_{provider.upper()}_MODEL_FALLBACKS")
        raw = env if env is not None else DEFAULT_MODEL_FALLBACKS.get(provider, "")
        out = [self.model_for(provider)]
        out += [m.strip() for m in raw.split(",") if m.strip() and m.strip() != out[0]]
        return out

    @property
    def request_timeout(self) -> float:
        reload_env()
        return float(os.getenv("GENESIS_TIMEOUT_S", "45"))

    @property
    def max_retries(self) -> int:
        reload_env()
        return max(0, min(3, int(os.getenv("GENESIS_MAX_RETRIES", "1"))))

    @property
    def max_output_tokens(self) -> int:
        reload_env()
        return int(os.getenv("GENESIS_MAX_OUTPUT_TOKENS", "4096"))

    @property
    def history_turns(self) -> int:
        reload_env()
        return int(os.getenv("GENESIS_HISTORY_TURNS", "12"))

    @property
    def port(self) -> int:
        reload_env()
        return int(os.getenv("GENESIS_PORT", "8100"))

    def access_token(self) -> str:
        """LAN access token for the device and web UI. Generated once, stored in .env."""
        tok = get_secret("GENESIS_ACCESS_TOKEN")
        if tok:
            return tok
        tok = secrets.token_urlsafe(18)
        try:
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "GENESIS_ACCESS_TOKEN", tok)
        except Exception:
            pass
        os.environ["GENESIS_ACCESS_TOKEN"] = tok
        return tok


settings = Settings()
