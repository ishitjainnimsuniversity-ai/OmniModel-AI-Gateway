"""
OmniModel Provider Registry and Metadata
Includes all 20 providers from the Master Reference + Local Offline Ollama.
"""

from typing import Dict, List, Any, Optional

PROVIDERS_METADATA: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini",
        "category": "Frontier Multimodal & Reasoning",
        "env_var": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-3.5-flash",
        "free_tier_available": True,
        "free_tier_note": "Generous free RPM on Google AI Studio without credit card",
        "free_key_url": "https://aistudio.google.com/app/apikey",
        "doc_url": "https://ai.google.dev/gemini-api/docs",
        "catalog_url": "https://ai.google.dev/gemini-api/docs/models",
        "format_type": "gemini",
        "models": [
            {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Ultra Fast & Stable)", "context": "1M", "speed": "Ultra Fast (<400ms)", "free": True, "tags": ["fast", "free_tier", "multimodal", "recommended"]},
            {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite (Instant)", "context": "1M", "speed": "Instant (<150ms)", "free": True, "tags": ["fast", "free_tier"]},
            {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Frontier)", "context": "1M", "speed": "High Quality", "free": True, "tags": ["frontier", "reasoning", "free_tier"]}
        ]
    },
    "groq": {
        "id": "groq",
        "name": "Groq LPU",
        "category": "Ultra Low-Latency Inference",
        "env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "free_tier_available": True,
        "free_tier_note": "Free tier with 30 RPM & blazing 500+ tokens/sec speeds",
        "free_key_url": "https://console.groq.com/keys",
        "doc_url": "https://console.groq.com/docs",
        "catalog_url": "https://console.groq.com/docs/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "context": "128k", "speed": "500+ tok/s", "free": True, "tags": ["speed", "coding", "free_tier"]},
            {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill Llama 70B", "context": "128k", "speed": "400+ tok/s", "free": True, "tags": ["reasoning", "math", "speed", "free_tier"]},
            {"id": "qwen-2.5-32b", "name": "Qwen 2.5 32B", "context": "128k", "speed": "600+ tok/s", "free": True, "tags": ["fast", "multilingual", "free_tier"]},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "context": "128k", "speed": "800+ tok/s", "free": True, "tags": ["ultra_fast", "free_tier"]}
        ]
    },
    "openrouter": {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "Unified Multi-Model Gateway & Free Models",
        "env_var": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openrouter/free",
        "free_tier_available": True,
        "free_tier_note": "Dedicated 100% FREE model pool with :free suffix",
        "free_key_url": "https://openrouter.ai/settings/keys",
        "doc_url": "https://openrouter.ai/docs",
        "catalog_url": "https://openrouter.ai/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "openrouter/free", "name": "OpenRouter Free Auto-Router (100% Free)", "context": "128k", "speed": "Fast", "free": True, "tags": ["reasoning", "free_tier", "coding"]},
            {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1 (100% Free)", "context": "64k", "speed": "Moderate", "free": True, "tags": ["reasoning", "free_tier", "coding"]},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (100% Free)", "context": "128k", "speed": "Fast", "free": True, "tags": ["general", "free_tier"]},
            {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash Exp (Free)", "context": "1M", "speed": "Ultra Fast", "free": True, "tags": ["multimodal", "free_tier"]},
            {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "name": "Qwen 2.5 Coder 32B (Free)", "context": "32k", "speed": "Fast", "free": True, "tags": ["coding", "free_tier"]},
            {"id": "anthropic/claude-3.7-sonnet", "name": "Claude 3.7 Sonnet (Router)", "context": "200k", "speed": "Frontier", "free": False, "tags": ["reasoning", "coding"]},
            {"id": "openai/gpt-4o", "name": "GPT-4o (Router)", "context": "128k", "speed": "Frontier", "free": False, "tags": ["multimodal", "general"]}
        ]
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek AI",
        "category": "Deep Reasoning & High-Performance Coding",
        "env_var": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-reasoner",
        "free_tier_available": True,
        "free_tier_note": "Includes initial free developer credits upon registration",
        "free_key_url": "https://platform.deepseek.com/api_keys",
        "doc_url": "https://api-docs.deepseek.com/",
        "catalog_url": "https://api-docs.deepseek.com/quick_start/pricing/",
        "format_type": "openai_compatible",
        "models": [
            {"id": "deepseek-reasoner", "name": "DeepSeek R1 (Reasoner)", "context": "64k", "speed": "Deep Thinking", "free": False, "tags": ["reasoning", "math", "deep_code"]},
            {"id": "deepseek-chat", "name": "DeepSeek V3 (Chat)", "context": "64k", "speed": "Fast", "free": False, "tags": ["coding", "general", "cheap"]}
        ]
    },
    "cerebras": {
        "id": "cerebras",
        "name": "Cerebras Cloud",
        "category": "Wafer-Scale Supercomputer Inference",
        "env_var": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "llama3.1-70b",
        "free_tier_available": True,
        "free_tier_note": "Generous free tier with world record 2000+ tokens/sec",
        "free_key_url": "https://cloud.cerebras.ai/",
        "doc_url": "https://inference-docs.cerebras.ai/",
        "catalog_url": "https://inference-docs.cerebras.ai/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "llama3.1-70b", "name": "Cerebras Llama 3.1 70B", "context": "128k", "speed": "1500+ tok/s", "free": True, "tags": ["extreme_speed", "free_tier"]},
            {"id": "llama3.1-8b", "name": "Cerebras Llama 3.1 8B", "context": "128k", "speed": "2000+ tok/s", "free": True, "tags": ["record_speed", "free_tier"]}
        ]
    },
    "sambanova": {
        "id": "sambanova",
        "name": "SambaNova Cloud",
        "category": "Full Precision & Giant Model Speed",
        "env_var": "SAMBANOVA_API_KEY",
        "base_url": "https://api.sambanova.ai/v1",
        "default_model": "Meta-Llama-3.3-70B-Instruct",
        "free_tier_available": True,
        "free_tier_note": "Free developer tier with high token throughput",
        "free_key_url": "https://cloud.sambanova.ai/",
        "doc_url": "https://docs.sambanova.ai/",
        "catalog_url": "https://docs.sambanova.ai/cloud/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "Meta-Llama-3.3-70B-Instruct", "name": "SambaNova Llama 3.3 70B", "context": "128k", "speed": "High Speed", "free": True, "tags": ["speed", "free_tier"]},
            {"id": "Meta-Llama-3.1-405B-Instruct", "name": "SambaNova Llama 3.1 405B", "context": "64k", "speed": "Frontier", "free": True, "tags": ["giant_model", "free_tier"]},
            {"id": "Qwen2.5-Coder-32B-Instruct", "name": "SambaNova Qwen 2.5 Coder 32B", "context": "32k", "speed": "Ultra Fast", "free": True, "tags": ["coding", "free_tier"]}
        ]
    },
    "huggingface": {
        "id": "huggingface",
        "name": "Hugging Face",
        "category": "Open-Source Hub & Serverless Router",
        "env_var": "HF_TOKEN",
        "base_url": "https://router.huggingface.co/openai/v1",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "free_tier_available": True,
        "free_tier_note": "Free community tier using User Access Tokens",
        "free_key_url": "https://huggingface.co/settings/tokens",
        "doc_url": "https://huggingface.co/docs/api-inference/",
        "catalog_url": "https://huggingface.co/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "name": "HF Llama 3.3 70B", "context": "128k", "speed": "Fast", "free": True, "tags": ["open_source", "free_tier"]},
            {"id": "mistralai/Mistral-7B-Instruct-v0.3", "name": "HF Mistral 7B Instruct", "context": "32k", "speed": "Fast", "free": True, "tags": ["open_source", "free_tier"]},
            {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "name": "HF DeepSeek R1 Qwen 32B", "context": "32k", "speed": "Moderate", "free": True, "tags": ["reasoning", "free_tier"]}
        ]
    },
    "cohere": {
        "id": "cohere",
        "name": "Cohere",
        "category": "Enterprise Search, Rerank & Command R+",
        "env_var": "COHERE_API_KEY",
        "base_url": "https://api.cohere.com/v2",
        "default_model": "command-r-plus-08-2024",
        "free_tier_available": True,
        "free_tier_note": "Free Trial key for developers for evaluation",
        "free_key_url": "https://dashboard.cohere.com/api-keys",
        "doc_url": "https://docs.cohere.com/",
        "catalog_url": "https://docs.cohere.com/reference/list-models",
        "format_type": "cohere",
        "models": [
            {"id": "command-r-plus-08-2024", "name": "Command R+ (Aug 2024)", "context": "128k", "speed": "High Quality", "free": True, "tags": ["enterprise", "rag", "citations"]},
            {"id": "command-r-08-2024", "name": "Command R", "context": "128k", "speed": "Fast", "free": True, "tags": ["fast_rag", "free_tier"]},
            {"id": "embed-english-v3.0", "name": "Cohere Embed English v3", "context": "512", "speed": "Instant", "free": True, "tags": ["embeddings"]}
        ]
    },
    "mistral": {
        "id": "mistral",
        "name": "Mistral AI",
        "category": "European Frontier Models & Codestral",
        "env_var": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "free_tier_available": True,
        "free_tier_note": "Free experimental access on La Plateforme",
        "free_key_url": "https://console.mistral.ai/api-keys/",
        "doc_url": "https://docs.mistral.ai/",
        "catalog_url": "https://docs.mistral.ai/api/endpoint/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "mistral-large-latest", "name": "Mistral Large 2411", "context": "128k", "speed": "High Quality", "free": False, "tags": ["reasoning", "multilingual", "coding"]},
            {"id": "codestral-latest", "name": "Codestral (Specialized Coding)", "context": "256k", "speed": "Fast", "free": False, "tags": ["coding", "code_fill"]},
            {"id": "mistral-small-latest", "name": "Mistral Small", "context": "32k", "speed": "Ultra Fast", "free": True, "tags": ["fast", "free_tier"]},
            {"id": "pixtral-large-latest", "name": "Pixtral Large (Vision)", "context": "128k", "speed": "High Quality", "free": False, "tags": ["vision", "multimodal"]}
        ]
    },
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "category": "Frontier GPT & o-Series Reasoning",
        "env_var": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "free_tier_available": False,
        "free_tier_note": "Pay-as-you-go credit balance",
        "free_key_url": "https://platform.openai.com/api-keys",
        "doc_url": "https://platform.openai.com/docs",
        "catalog_url": "https://platform.openai.com/docs/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o (Omni)", "context": "128k", "speed": "Fast", "free": False, "tags": ["multimodal", "frontier", "coding"]},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": "128k", "speed": "Ultra Fast", "free": False, "tags": ["fast", "cheap", "vision"]},
            {"id": "o3-mini", "name": "o3-mini (Reasoning)", "context": "200k", "speed": "Deep Reasoning", "free": False, "tags": ["reasoning", "math", "science"]},
            {"id": "o1", "name": "o1 (Flagship Reasoning)", "context": "200k", "speed": "Deliberate", "free": False, "tags": ["flagship_reasoning", "coding"]}
        ]
    },
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "category": "Frontier Coding, Artifacts & Complex Reasoning",
        "env_var": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-7-sonnet-20250219",
        "free_tier_available": False,
        "free_tier_note": "Requires initial API credit top-up",
        "free_key_url": "https://console.anthropic.com/settings/keys",
        "doc_url": "https://docs.anthropic.com/",
        "catalog_url": "https://docs.anthropic.com/en/docs/about-claude/models",
        "format_type": "anthropic",
        "models": [
            {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet (Hybrid Reasoning)", "context": "200k", "speed": "Adaptive", "free": False, "tags": ["frontier_code", "hybrid_reasoning", "best_coding"]},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet v2", "context": "200k", "speed": "High Quality", "free": False, "tags": ["coding", "vision", "nuance"]},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context": "200k", "speed": "Blazing Fast", "free": False, "tags": ["speed", "low_cost"]}
        ]
    },
    "together": {
        "id": "together",
        "name": "Together AI",
        "category": "Open-Source Cloud & Fine-Tuning",
        "env_var": "TOGETHER_API_KEY",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "free_tier_available": True,
        "free_tier_note": "$5 Free credit for new accounts",
        "free_key_url": "https://api.together.ai/settings/api-keys",
        "doc_url": "https://docs.together.ai/",
        "catalog_url": "https://api.together.xyz/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Together Llama 3.3 70B Turbo", "context": "128k", "speed": "Fast", "free": False, "tags": ["speed", "open_weight"]},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "Together DeepSeek R1", "context": "128k", "speed": "Moderate", "free": False, "tags": ["reasoning", "coding"]},
            {"id": "black-forest-labs/FLUX.1-schnell", "name": "Flux.1 Schnell (Image)", "context": "N/A", "speed": "Instant", "free": False, "tags": ["image"]}
        ]
    },
    "fireworks": {
        "id": "fireworks",
        "name": "Fireworks AI",
        "category": "Compound AI & Production Inference",
        "env_var": "FIREWORKS_API_KEY",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "free_tier_available": True,
        "free_tier_note": "$1 Free credit on signup",
        "free_key_url": "https://fireworks.ai/account/api-keys",
        "doc_url": "https://docs.fireworks.ai/",
        "catalog_url": "https://fireworks.ai/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "accounts/fireworks/models/llama-v3p3-70b-instruct", "name": "Fireworks Llama 3.3 70B", "context": "128k", "speed": "Ultra Fast", "free": False, "tags": ["speed", "production"]},
            {"id": "accounts/fireworks/models/deepseek-r1", "name": "Fireworks DeepSeek R1", "context": "128k", "speed": "High Speed", "free": False, "tags": ["reasoning", "math"]},
            {"id": "accounts/fireworks/models/qwen2p5-coder-32b-instruct", "name": "Fireworks Qwen 2.5 Coder 32B", "context": "32k", "speed": "Fast", "free": False, "tags": ["coding"]}
        ]
    },
    "perplexity": {
        "id": "perplexity",
        "name": "Perplexity AI",
        "category": "Real-Time Web Search & Grounding",
        "env_var": "PERPLEXITY_API_KEY",
        "base_url": "https://api.perplexity.ai",
        "default_model": "sonar",
        "free_tier_available": False,
        "free_tier_note": "API credits available via subscription or prepaid",
        "free_key_url": "https://www.perplexity.ai/settings/api",
        "doc_url": "https://docs.perplexity.ai/",
        "catalog_url": "https://docs.perplexity.ai/getting-started/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "sonar-reasoning-pro", "name": "Sonar Reasoning Pro (Search + R1)", "context": "128k", "speed": "Deliberate", "free": False, "tags": ["search", "citations", "reasoning"]},
            {"id": "sonar-pro", "name": "Sonar Pro (Deep Web Search)", "context": "200k", "speed": "Fast", "free": False, "tags": ["search", "citations", "research"]},
            {"id": "sonar", "name": "Sonar (Fast Web Search)", "context": "128k", "speed": "Ultra Fast", "free": False, "tags": ["search", "fast"]}
        ]
    },
    "xai": {
        "id": "xai",
        "name": "xAI Grok",
        "category": "Truth-Seeking & Real-Time Context",
        "env_var": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-1212",
        "free_tier_available": True,
        "free_tier_note": "$25/mo free promotional credits for verified accounts",
        "free_key_url": "https://console.x.ai/",
        "doc_url": "https://docs.x.ai/",
        "catalog_url": "https://docs.x.ai/developers/rest-api-reference/inference/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "grok-2-1212", "name": "Grok 2 (Latest)", "context": "128k", "speed": "Fast", "free": False, "tags": ["reasoning", "coding", "general"]},
            {"id": "grok-2-vision-1212", "name": "Grok 2 Vision", "context": "32k", "speed": "Fast", "free": False, "tags": ["vision", "multimodal"]}
        ]
    },
    "replicate": {
        "id": "replicate",
        "name": "Replicate",
        "category": "Generative Media, Vision & Custom AI",
        "env_var": "REPLICATE_API_TOKEN",
        "base_url": "https://api.replicate.com/v1",
        "default_model": "black-forest-labs/flux-schnell",
        "free_tier_available": True,
        "free_tier_note": "Initial free compute credits on signup",
        "free_key_url": "https://replicate.com/account/api-tokens",
        "doc_url": "https://replicate.com/docs",
        "catalog_url": "https://replicate.com/explore",
        "format_type": "replicate",
        "models": [
            {"id": "black-forest-labs/flux-schnell", "name": "Flux Schnell (Fast Image)", "context": "N/A", "speed": "Instant", "free": False, "tags": ["image", "generation"]},
            {"id": "openai/whisper", "name": "Whisper Large v3 (Audio)", "context": "N/A", "speed": "Fast", "free": False, "tags": ["audio", "transcription"]},
            {"id": "meta/meta-llama-3-70b-instruct", "name": "Replicate Llama 3 70B", "context": "8k", "speed": "Fast", "free": False, "tags": ["text"]}
        ]
    },
    "stability": {
        "id": "stability",
        "name": "Stability AI",
        "category": "State of the Art Generative Media",
        "env_var": "STABILITY_API_KEY",
        "base_url": "https://api.stability.ai/v2beta/stable-image/generate",
        "default_model": "sd3.5-large",
        "free_tier_available": True,
        "free_tier_note": "Free initial credits on account creation",
        "free_key_url": "https://platform.stability.ai/account/keys",
        "doc_url": "https://platform.stability.ai/docs",
        "catalog_url": "https://platform.stability.ai/docs/getting-started",
        "format_type": "stability",
        "models": [
            {"id": "sd3.5-large", "name": "Stable Diffusion 3.5 Large", "context": "N/A", "speed": "High Res", "free": False, "tags": ["image", "diffusion"]},
            {"id": "core", "name": "Stable Image Core", "context": "N/A", "speed": "Fast", "free": False, "tags": ["image", "photorealism"]}
        ]
    },
    "ai21": {
        "id": "ai21",
        "name": "AI21 Labs",
        "category": "Jamba Hybrid Mamba-Transformer Architecture",
        "env_var": "AI21_API_KEY",
        "base_url": "https://api.ai21.com/studio/v1",
        "default_model": "jamba-1.5-mini",
        "free_tier_available": True,
        "free_tier_note": "$10 Free credits on signup",
        "free_key_url": "https://studio.ai21.com/account/api-key",
        "doc_url": "https://docs.ai21.com/",
        "catalog_url": "https://docs.ai21.com/",
        "format_type": "openai_compatible",
        "models": [
            {"id": "jamba-1.5-large", "name": "Jamba 1.5 Large", "context": "256k", "speed": "Fast", "free": False, "tags": ["mamba", "long_context"]},
            {"id": "jamba-1.5-mini", "name": "Jamba 1.5 Mini", "context": "256k", "speed": "Ultra Fast", "free": False, "tags": ["mamba", "speed"]}
        ]
    },
    "azure": {
        "id": "azure",
        "name": "Azure AI / Foundry",
        "category": "Enterprise Cloud Models",
        "env_var": "AZURE_API_KEY",
        "base_url": "https://your-resource.openai.azure.com",
        "default_model": "gpt-4o",
        "free_tier_available": False,
        "free_tier_note": "Enterprise subscription",
        "free_key_url": "https://portal.azure.com/",
        "doc_url": "https://learn.microsoft.com/azure/foundry/",
        "catalog_url": "https://ai.azure.com/explore/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "gpt-4o", "name": "Azure GPT-4o", "context": "128k", "speed": "Enterprise SLA", "free": False, "tags": ["enterprise", "sla"]}
        ]
    },
    "bedrock": {
        "id": "bedrock",
        "name": "Amazon Bedrock",
        "category": "AWS Multi-Model Catalog",
        "env_var": "AWS_ACCESS_KEY_ID",
        "base_url": "https://bedrock-runtime.us-east-1.amazonaws.com",
        "default_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "free_tier_available": False,
        "free_tier_note": "AWS Free Tier applies to select services",
        "free_key_url": "https://console.aws.amazon.com/iam/home#/security_credentials",
        "doc_url": "https://docs.aws.amazon.com/bedrock/",
        "catalog_url": "https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html",
        "format_type": "bedrock",
        "models": [
            {"id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "name": "Bedrock Claude 3.5 Sonnet", "context": "200k", "speed": "Enterprise", "free": False, "tags": ["enterprise", "aws"]}
        ]
    },
    "ollama": {
        "id": "ollama",
        "name": "Local Ollama / OpenJarvis Local Engine",
        "category": "100% Free Local Offline Privacy",
        "env_var": "OLLAMA_BASE_URL",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2:1b",
        "free_tier_available": True,
        "free_tier_note": "100% Free, runs locally on your GPU/CPU without internet",
        "free_key_url": "https://ollama.ai/",
        "doc_url": "https://github.com/ollama/ollama",
        "catalog_url": "https://ollama.ai/library",
        "format_type": "openai_compatible",
        "models": [
            {"id": "llama3.2:1b", "name": "Ollama Llama 3.2 1B (Installed Local)", "context": "128k", "speed": "Local Hardware", "free": True, "tags": ["local", "offline", "privacy", "free_tier"]},
            {"id": "llama3.2:latest", "name": "Ollama Llama 3.2 (Local)", "context": "128k", "speed": "Local Hardware", "free": True, "tags": ["local", "offline", "privacy", "free_tier"]}
        ]
    },
    "pollinations": {
        "id": "pollinations",
        "name": "Pollinations Frontier Cloud AI (Zero-Key)",
        "category": "100% Free Keyless Frontier Models",
        "env_var": None,
        "base_url": "https://text.pollinations.ai/openai",
        "default_model": "openai",
        "free_tier_available": True,
        "free_tier_note": "100% Free Keyless Cloud GPT-4o, Llama 3.3 & DeepSeek R1",
        "free_key_url": "https://pollinations.ai/",
        "doc_url": "https://pollinations.ai/",
        "catalog_url": "https://text.pollinations.ai/models",
        "format_type": "openai_compatible",
        "models": [
            {"id": "openai", "name": "GPT-4o Mini / OpenAI (Keyless Cloud)", "context": "128k", "speed": "Fast", "free": True, "tags": ["fast", "free_tier", "general", "coding"]},
            {"id": "deepseek", "name": "DeepSeek V3 / R1 (Keyless Cloud)", "context": "64k", "speed": "Fast", "free": True, "tags": ["reasoning", "coding", "free_tier"]},
            {"id": "mistral", "name": "Mistral Small 3 (Keyless Cloud)", "context": "32k", "speed": "Ultra Fast", "free": True, "tags": ["speed", "free_tier"]}
        ]    },
    "freellmapi": {
        "id": "freellmapi",
        "name": "FreeLLMAPI Unified Pool",
        "category": "Free Tier Key Aggregator (~10.1B tokens/mo)",
        "env_var": "FREELLMAPI_API_KEY",
        "base_url": "http://localhost:3001/v1",
        "default_model": "auto",
        "free_tier_available": True,
        "free_tier_note": "Aggregates free tiers of Google, Groq, Cerebras, OpenRouter & Mistral behind 1 address",
        "free_key_url": "http://localhost:3001",
        "doc_url": "https://github.com/tashfeenahmed/freellmapi",
        "catalog_url": "https://freellmapi.co/models.html",
        "format_type": "openai_compatible",
        "models": [
            {"id": "auto", "name": "FreeLLMAPI Auto-Switcher (100% Free)", "context": "128k", "speed": "Auto Fast", "free": True, "tags": ["free_tier", "auto_fallback", "coding"]},
            {"id": "gemini-flash", "name": "FreeLLMAPI / Gemini Flash", "context": "1M", "speed": "Fast", "free": True, "tags": ["free_tier", "multimodal"]},
            {"id": "groq-llama", "name": "FreeLLMAPI / Groq Llama 3.3", "context": "128k", "speed": "500+ tok/s", "free": True, "tags": ["speed", "free_tier"]},
            {"id": "cerebras-llama", "name": "FreeLLMAPI / Cerebras", "context": "128k", "speed": "2000+ tok/s", "free": True, "tags": ["speed", "free_tier"]}
        ]
    },
    "omniroute": {
        "id": "omniroute",
        "name": "OmniRoute Compressed Pool",
        "category": "Free Model Aggregator & Token Compressor (~1.62B tokens/mo)",
        "env_var": "OMNIROUTE_API_KEY",
        "base_url": "http://localhost:20128/v1",
        "default_model": "auto",
        "free_tier_available": True,
        "free_tier_note": "Pools free models with 15–95% token compression (OpenCode Zen, NVIDIA, Cloudflare, Groq)",
        "free_key_url": "http://localhost:20128",
        "doc_url": "https://github.com/cheaper-inference/OmniRoute",
        "catalog_url": "https://github.com/cheaper-inference/OmniRoute",
        "format_type": "openai_compatible",
        "models": [
            {"id": "auto", "name": "OmniRoute Compressed Auto (100% Free)", "context": "128k", "speed": "Compressed", "free": True, "tags": ["free_tier", "compression", "coding"]},
            {"id": "opencode-zen", "name": "OmniRoute / OpenCode Zen", "context": "64k", "speed": "Coding", "free": True, "tags": ["coding", "free_tier"]},
            {"id": "nvidia-nim", "name": "OmniRoute / NVIDIA NIM", "context": "128k", "speed": "Fast", "free": True, "tags": ["frontier", "free_tier"]},
            {"id": "cloudflare-ai", "name": "OmniRoute / Cloudflare AI", "context": "128k", "speed": "Edge", "free": True, "tags": ["edge", "free_tier"]}
        ]
    },
    "nvidia_nim": {
        "id": "nvidia_nim",
        "name": "NVIDIA NIM Free Microservices",
        "category": "Enterprise GPU Cloud Free Tier (1,000 Free Credits)",
        "env_var": "NVIDIA_NIM_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "meta/llama-3.3-70b-instruct",
        "free_tier_available": True,
        "free_tier_note": "1,000 free API calls without credit card on build.nvidia.com",
        "free_key_url": "https://build.nvidia.com/",
        "doc_url": "https://docs.nvidia.com/nim/",
        "catalog_url": "https://build.nvidia.com/explore/discover",
        "format_type": "openai_compatible",
        "models": [
            {"id": "meta/llama-3.3-70b-instruct", "name": "NVIDIA / Llama 3.3 70B Instruct", "context": "128k", "speed": "High Speed", "free": True, "tags": ["frontier", "free_tier", "coding"]},
            {"id": "deepseek-ai/deepseek-r1", "name": "NVIDIA / DeepSeek R1 Reasoning", "context": "64k", "speed": "Deep Thinking", "free": True, "tags": ["reasoning", "free_tier", "math"]},
            {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "NVIDIA / Nemotron 70B", "context": "128k", "speed": "Fast", "free": True, "tags": ["general", "free_tier"]}
        ]
    },
    "cloudflare_ai": {
        "id": "cloudflare_ai",
        "name": "Cloudflare Workers AI",
        "category": "Serverless Edge GPU (10,000 Neurons/Day Free)",
        "env_var": "CLOUDFLARE_API_KEY",
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "default_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "free_tier_available": True,
        "free_tier_note": "10,000 free neurons daily without credit card across edge datacenters",
        "free_key_url": "https://dash.cloudflare.com/",
        "doc_url": "https://developers.cloudflare.com/workers-ai/",
        "catalog_url": "https://developers.cloudflare.com/workers-ai/models/",
        "format_type": "openai_compatible",
        "models": [
            {"id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "name": "Cloudflare / Llama 3.3 70B Fast", "context": "128k", "speed": "Edge Ultra-Fast", "free": True, "tags": ["edge", "free_tier"]},
            {"id": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", "name": "Cloudflare / DeepSeek R1 32B", "context": "64k", "speed": "Reasoning", "free": True, "tags": ["reasoning", "free_tier"]}
        ]
    }
}

