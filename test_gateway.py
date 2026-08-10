"""
Automated Test Suite for OmniModel Gateway
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.providers import PROVIDERS_METADATA
from core.config import GatewayConfig
from core.router import SmartRouter
from antigravity_bridge import OmniAI

def test_metadata_integrity():
    print("Testing Provider Metadata Integrity...")
    assert len(PROVIDERS_METADATA) >= 20, f"Expected 20+ providers, got {len(PROVIDERS_METADATA)}"
    
    expected_providers = [
        "gemini", "groq", "openrouter", "deepseek", "cerebras", "sambanova",
        "huggingface", "cohere", "mistral", "openai", "anthropic", "together",
        "fireworks", "perplexity", "xai", "replicate", "stability", "ai21",
        "azure", "bedrock"
    ]
    for p in expected_providers:
        assert p in PROVIDERS_METADATA, f"Provider '{p}' missing from registry!"
        meta = PROVIDERS_METADATA[p]
        assert "name" in meta
        assert "default_model" in meta
        assert len(meta.get("models", [])) > 0
    print(f"[OK] All {len(PROVIDERS_METADATA)} providers verified with active model catalogs!")

def test_intent_routing():
    print("\nTesting Smart Intent Classifier...")
    
    # 1. Code intent
    profile, conf, rationale = SmartRouter.classify_intent("Write a Python script to calculate Fibonacci numbers with memoization")
    print(f"Prompt: 'Write a Python script...' -> Profile: {profile} ({conf*100:.0f}%)")
    assert profile == "coding"

    # 2. Reasoning intent
    profile, conf, rationale = SmartRouter.classify_intent("Prove by induction that 1 + 2 + ... + n = n(n+1)/2 step by step")
    print(f"Prompt: 'Prove by induction...' -> Profile: {profile} ({conf*100:.0f}%)")
    assert profile == "reasoning"

    # 3. Free tier intent
    profile, conf, rationale = SmartRouter.classify_intent("Tell me a free zero cost AI solution")
    print(f"Prompt: 'free zero cost AI...' -> Profile: {profile} ({conf*100:.0f}%)")
    assert profile == "free_tier"

    # 4. Search intent
    profile, conf, rationale = SmartRouter.classify_intent("What is the latest news and weather today in Tokyo in 2026?")
    print(f"Prompt: 'latest news today...' -> Profile: {profile} ({conf*100:.0f}%)")
    assert profile == "search"

    print("[OK] Intent classification test passed!")

def test_sdk_bridge():
    print("\nTesting Antigravity SDK Bridge...")
    ai = OmniAI()
    providers = ai.list_providers()
    models = ai.list_models()
    print(f"Active Provider Profiles: {len(providers)}")
    print(f"Total Models in Gateway: {len(models)}")
    assert len(models) >= 40
    print("[OK] Antigravity SDK Bridge initialized successfully!")

if __name__ == "__main__":
    print("==================================================")
    print("Running OmniModel Gateway Test Suite")
    print("==================================================")
    test_metadata_integrity()
    test_intent_routing()
    test_sdk_bridge()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
