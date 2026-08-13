"""
Intelligent Intent Classifier, Smart Router and Auto-Fallback Waterfall Engine
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from core.providers import PROVIDERS_METADATA
from core.config import GatewayConfig
from core.adapters import UniversalAdapter

class SmartRouter:
    ROUTING_PROFILES = {
        "speed": {
            "name": "⚡ Ultra-Fast Speed (<150ms)",
            "description": "Blazing fast inference via custom LPU/wafer hardware",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("groq", "llama-3.3-70b-versatile"),
                ("cerebras", "llama3.1-70b"),
                ("sambanova", "Meta-Llama-3.3-70B-Instruct"),
                ("openrouter", "meta-llama/llama-3.3-70b-instruct:free")
            ]
        },
        "reasoning": {
            "name": "🧠 Deep Reasoning & Math",
            "description": "Complex chain-of-thought, mathematical proof, logic and deep planning",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("gemini", "gemma-4-31b-it"),
                ("deepseek", "deepseek-reasoner"),
                ("groq", "deepseek-r1-distill-llama-70b"),
                ("openrouter", "deepseek/deepseek-r1:free"),
                ("openai", "o3-mini"),
                ("anthropic", "claude-3-7-sonnet-20250219")
            ]
        },
        "coding": {
            "name": "💻 Elite Software Architecture & Code",
            "description": "Complex full-stack coding, refactoring, debugging and algorithmic synthesis",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("anthropic", "claude-3-7-sonnet-20250219"),
                ("mistral", "codestral-latest"),
                ("openrouter", "qwen/qwen-2.5-coder-32b-instruct:free"),
                ("openai", "gpt-4o"),
                ("deepseek", "deepseek-chat")
            ]
        },
        "search": {
            "name": "🌐 Live Web Search & Grounding",
            "description": "Real-time web retrieval, current news, fact checking and source citations",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("perplexity", "sonar"),
                ("openrouter", "google/gemini-2.0-flash-exp:free")
            ]
        },
        "free_tier": {
            "name": "🆓 100% Zero-Cost / Free Tier",
            "description": "Auto-routes to verified 100% free models without credit card requirements",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("openrouter", "deepseek/deepseek-r1:free"),
                ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
                ("groq", "llama-3.3-70b-versatile"),
                ("huggingface", "meta-llama/Llama-3.3-70B-Instruct"),
                ("cerebras", "llama3.1-70b"),
                ("sambanova", "Meta-Llama-3.3-70B-Instruct"),
                ("ollama", "llama3.2:latest")
            ]
        },
        "general": {
            "name": "⚖️ Balanced Frontier Intelligence",
            "description": "Optimal balance of quality, speed and conversational fluency",
            "chain": [
                ("gemini", "gemini-flash-latest"),
                ("groq", "llama-3.3-70b-versatile"),
                ("openai", "gpt-4o"),
                ("anthropic", "claude-3-5-sonnet-20241022"),
                ("mistral", "mistral-large-latest"),
                ("openrouter", "deepseek/deepseek-r1:free")
            ]
        }
    }

    @classmethod
    def classify_intent(cls, prompt: str) -> Tuple[str, float, str]:
        """
        Classifies user prompt intent into a routing profile:
        Returns: (profile_key, confidence_score, rationale)
        """
        text = prompt.lower().strip()

        # Check for explicit code keywords
        code_patterns = [r"\bdef\b", r"\bclass\b", r"\bfunction\b", r"\bimport\b", r"\bconst\b", r"```", r"\bsql\b", r"\bapi\b", r"\bdebug\b", r"\brefactor\b", r"\btypescript\b", r"\bpython\b", r"\breact\b", r"\bhtml\b", r"\bcss\b"]
        if any(re.search(p, text) for p in code_patterns):
            return "coding", 0.92, "Detected software development, programming syntax or refactoring intent."

        # Check for reasoning / math keywords
        reasoning_patterns = [r"\bprove\b", r"\bstep by step\b", r"\bcalculate\b", r"\btheorem\b", r"\briddle\b", r"\bderive\b", r"\bprobability\b", r"\blogic\b", r"\bquantum\b", r"\banalyze deeply\b", r"\bcomplex reasoning\b"]
        if any(re.search(p, text) for p in reasoning_patterns):
            return "reasoning", 0.89, "Detected logical deduction, mathematical proof or multi-step reasoning."

        # Check for real-time / web search keywords
        search_patterns = [r"\btoday\b", r"\byesterday\b", r"\blatest news\b", r"\bweather in\b", r"\bwho won\b", r"\bcurrent price\b", r"\b2026\b", r"\b2025\b", r"\brecent\b", r"\bbreaking news\b"]
        if any(re.search(p, text) for p in search_patterns):
            return "search", 0.95, "Detected temporal inquiry or live web information requirement."

        # Check for speed / fast response keywords
        speed_patterns = [r"\bquick\b", r"\bfast\b", r"\bsummarize briefly\b", r"\btl;dr\b", r"\bone sentence\b", r"\brapid\b", r"\binstant\b"]
        if any(re.search(p, text) for p in speed_patterns):
            return "speed", 0.85, "Optimized for ultra-low latency response."

        # Check for free tier request
        if "free" in text or "zero cost" in text or "no api key" in text:
            return "free_tier", 0.98, "User explicitly requested free tier or zero-cost models."

        return "general", 0.75, "Balanced conversational synthesis across frontier models."

    @classmethod
    async def route_and_execute_stream(
        cls,
        messages: List[Dict[str, str]],
        profile_override: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes smart routing with automatic multi-provider fallback waterfall.
        """
        last_prompt = messages[-1].get("content", "") if messages else ""
        if profile_override and profile_override in cls.ROUTING_PROFILES:
            profile_key = profile_override
            rationale = f"Manual override: {cls.ROUTING_PROFILES[profile_key]['name']}"
            confidence = 1.0
        else:
            profile_key, confidence, rationale = cls.classify_intent(last_prompt)

        profile = cls.ROUTING_PROFILES[profile_key]
        chain = profile["chain"]

        # Yield routing metadata header
        yield {
            "meta_event": "routing_decision",
            "profile": profile_key,
            "profile_name": profile["name"],
            "rationale": rationale,
            "confidence": confidence,
            "chain": [{"provider": p, "model": m, "provider_name": PROVIDERS_METADATA.get(p, {}).get("name", p)} for p, m in chain]
        }

        # Try providers down the waterfall chain
        success = False
        attempted_providers = []

        for provider_id, model in chain:
            meta = PROVIDERS_METADATA.get(provider_id, {})
            env_var = meta.get("env_var")
            has_key = bool(GatewayConfig.get_key(env_var)) if env_var else False

            # Special case for free tier: if openrouter or groq key exists, or if testing
            attempted_providers.append(f"{meta.get('name', provider_id)} ({model})")

            yield {
                "meta_event": "attempting_provider",
                "provider": provider_id,
                "provider_name": meta.get("name", provider_id),
                "model": model
            }

            got_content = False
            had_error = False

            async for chunk in UniversalAdapter.chat_stream(
                provider_id=provider_id,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if chunk.get("error") or chunk.get("status") == "missing_key":
                    had_error = True
                    # Yield warning before fallback
                    yield {
                        "meta_event": "provider_fallback",
                        "failed_provider": meta.get("name", provider_id),
                        "reason": chunk.get("delta", "Provider unavailable or key not configured")
                    }
                    break
                else:
                    got_content = True
                    yield chunk

            if got_content and not had_error:
                success = True
                break

        if not success:
            # All providers in chain had no active keys or failed. Provide helpful unified gateway setup instructions.
            help_message = (
                f"\n\n### ⚡ OmniModel Gateway Status\n"
                f"Attempted waterfall chain: {', '.join(attempted_providers)}.\n\n"
                f"**To activate any provider for instant live generation:**\n"
                f"1. **Google Gemini (Free Tier)**: Get free key at [Google AI Studio](https://aistudio.google.com/app/apikey) and paste in dashboard or `.env` as `GEMINI_API_KEY`.\n"
                f"2. **Groq (Free Tier, 500+ tok/s)**: Get key at [Groq Console](https://console.groq.com/keys) as `GROQ_API_KEY`.\n"
                f"3. **OpenRouter (100% Free Models)**: Get free key at [OpenRouter](https://openrouter.ai/settings/keys) as `OPENROUTER_API_KEY`.\n"
                f"4. **DeepSeek / Claude / OpenAI / Mistral**: Add your corresponding keys.\n"
                f"5. **Local Offline AI**: Run `ollama run llama3.2` locally for zero-config offline AI!"
            )
            yield {
                "delta": help_message,
                "done": True,
                "provider": "omnimodel_gateway",
                "model": "router_fallback"
            }
