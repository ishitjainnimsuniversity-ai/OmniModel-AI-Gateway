"""
Configuration and Environment Manager for OmniModel Gateway
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Initial load
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)
else:
    load_dotenv(override=True)

class GatewayConfig:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")

    @classmethod
    def reload_env(cls):
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE, override=True)

    @classmethod
    def get_key(cls, env_var: str) -> Optional[str]:
        val = os.getenv(env_var)
        if val and val.strip():
            return val.strip()
        return None

    @classmethod
    def set_key(cls, env_var: str, value: str) -> bool:
        try:
            if not ENV_FILE.exists():
                ENV_FILE.touch()
            set_key(str(ENV_FILE), env_var, value)
            os.environ[env_var] = value
            return True
        except Exception as e:
            print(f"Error setting key {env_var}: {e}")
            return False

    @classmethod
    def get_active_providers_status(cls, providers_dict: Dict[str, Any]) -> Dict[str, Any]:
        cls.reload_env()
        status_map = {}
        for pid, meta in providers_dict.items():
            env_var = meta.get("env_var")
            key_val = os.getenv(env_var) if env_var else None
            has_key = bool(key_val and len(key_val.strip()) > 3)
            
            # Special case for local ollama
            if pid == "ollama":
                has_key = True

            status_map[pid] = {
                "id": pid,
                "name": meta["name"],
                "category": meta["category"],
                "has_key": has_key,
                "env_var": env_var,
                "free_tier": meta.get("free_tier_available", False),
                "free_note": meta.get("free_tier_note", ""),
                "free_key_url": meta.get("free_key_url", ""),
                "default_model": meta.get("default_model", ""),
                "models": meta.get("models", [])
            }
        return status_map
