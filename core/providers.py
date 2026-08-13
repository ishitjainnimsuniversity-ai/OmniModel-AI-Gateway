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
        "default_model": "gemini-flash-latest",
        "free_tier_available": True,
        "free_tier_note": "Generous free RPM on Google AI Studio without credit card",
        "free_key_url": "https://aistudio.google.com/app/apikey",
        "doc_url": "https://ai.google.dev/gemini-api/docs",
        "catalog_url": "https://ai.google.dev/gemini-api/docs/models",
        "format_type": "gemini",
        "models": [
            {"id": "gemini-flash-latest", "name": "Gemini Flash Latest", "context": "1M", "speed": "Ultra Fast", "free": True, "tags": ["fast", "multimodal", "free_tier", "search"]},
            {"id": "gemma-4-31b-it", "name": "Gemma 4 31B IT", "context": "128k", "speed": "Fast", "free": True, "tags": ["reasoning", "math", "code", "free_tier"]},
            {"id": "gemini-pro-latest", "name": "Gemini Pro Latest", "context": "2M", "speed": "High Quality", "free": True, "tags": ["frontier", "coding", "complex", "free_tier"]}
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
        "default_model": "deepseek/deepseek-r1:free",
        "free_tier_available": True,
        "free_tier_note": "Dedicated 100% FREE model pool with :free suffix",
        "free_key_url": "https://openrouter.ai/settings/keys",
        "doc_url": "https://openrouter.ai/docs",
        "catalog_url": "https://openrouter.ai/models",
        "format_type": "openai_compatible",
        "models": [
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
        "name": "Local Ollama / LM Studio",
        "category": "100% Free Local Offline Privacy",
        "env_var": "OLLAMA_BASE_URL",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2:latest",
        "free_tier_available": True,
        "free_tier_note": "100% Free, runs locally on your GPU/CPU without internet",
        "free_key_url": "https://ollama.ai/",
        "doc_url": "https://github.com/ollama/ollama",
        "catalog_url": "https://ollama.ai/library",
        "format_type": "openai_compatible",
        "models": [
            {"id": "llama3.2:latest", "name": "Ollama Llama 3.2 (Local)", "context": "128k", "speed": "Local Hardware", "free": True, "tags": ["local", "offline", "privacy", "free_tier"]},
            {"id": "deepseek-r1:latest", "name": "Ollama DeepSeek R1 (Local)", "context": "32k", "speed": "Local Hardware", "free": True, "tags": ["local", "reasoning", "free_tier"]},
            {"id": "qwen2.5-coder:latest", "name": "Ollama Qwen 2.5 Coder (Local)", "context": "32k", "speed": "Local Hardware", "free": True, "tags": ["local", "coding", "free_tier"]}
        ]
    }
}
