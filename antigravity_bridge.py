"""
Antigravity OmniModel Bridge SDK
Allows native Antigravity scripts, agents, and workflows to query any of the 20 AI providers or smart auto-route seamlessly.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Generator

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.config import GatewayConfig
from core.providers import PROVIDERS_METADATA
from core.adapters import UniversalAdapter
from core.router import SmartRouter

class OmniAI:
    def __init__(self):
        GatewayConfig.reload_env()

    @classmethod
    def list_providers(cls) -> Dict[str, Any]:
        """Returns status of all 20 AI providers"""
        return GatewayConfig.get_active_providers_status(PROVIDERS_METADATA)

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """Returns flattened list of all models across providers"""
        all_models = []
        for pid, meta in PROVIDERS_METADATA.items():
            for m in meta.get("models", []):
                all_models.append({
                    "id": f"{pid}/{m['id']}",
                    "raw_id": m["id"],
                    "provider": pid,
                    "provider_name": meta["name"],
                    "name": m["name"],
                    "context": m.get("context", "128k"),
                    "speed": m.get("speed", "Fast"),
                    "free": m.get("free", False),
                    "tags": m.get("tags", [])
                })
        return all_models

    @classmethod
    def chat(
        cls,
        prompt: Union[str, List[Dict[str, str]]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        profile: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        Main query method:
        - If provider is specified, queries that provider directly.
        - If provider is None, uses SmartRouter to automatically classify and route.
        """
        # Format messages
        if isinstance(prompt, str):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
        else:
            messages = prompt
            if system_prompt and not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": system_prompt})

        async def _run_async():
            if provider:
                # Direct provider query
                target_model = model or PROVIDERS_METADATA.get(provider, {}).get("default_model", "")
                chunks = []
                async for chunk in UniversalAdapter.chat_stream(
                    provider_id=provider,
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    delta = chunk.get("delta", "")
                    if delta:
                        chunks.append(delta)
                return "".join(chunks)
            else:
                # Smart route
                chunks = []
                async for chunk in SmartRouter.route_and_execute_stream(
                    messages=messages,
                    profile_override=profile,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    delta = chunk.get("delta", "")
                    if delta:
                        chunks.append(delta)
                return "".join(chunks)

        # Run event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(_run_async())
            else:
                return asyncio.run(_run_async())
        except Exception:
            return asyncio.run(_run_async())

class GenesisAI(OmniAI):
    """GENESIS AI 5.0 Universal Cognitive Multi-Model Engine"""
    pass

class AlfaAI(GenesisAI):
    pass

# Quick CLI test
if __name__ == "__main__":
    genesis = GenesisAI()
    print("=======================================================")
    print("GENESIS AI 5.0 Universal Cognitive Bridge initialized!")
    print(f"Total Providers: {len(PROVIDERS_METADATA)}")
    print(f"Total Models Cataloged: {len(genesis.list_models())}")
    print("=======================================================")
    test_prompt = "Say hello from GENESIS AI 5.0 in one sentence!"
    print(f"\nTesting GENESIS AI 5.0 Smart Router with prompt: '{test_prompt}'\n")
    res = genesis.chat(test_prompt, profile="free_tier")
    print(res)
