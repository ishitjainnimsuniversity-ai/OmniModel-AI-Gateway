"""
Intelligent Intent Classifier, Smart Router and Auto-Fallback Waterfall Engine
GENESIS AI 5.0 Dual-Brain Architecture (Local Offline Ollama + Cloud Frontier AI)
"""

import ast
import asyncio
import math
import operator
import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor, wait as cf_wait
import urllib.parse
import httpx
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from core.providers import PROVIDERS_METADATA
from core.config import GatewayConfig
from core.adapters import UniversalAdapter


def _is_cloud_env() -> bool:
    return bool(
        os.getenv("VERCEL")
        or os.getenv("VERCEL_ENV")
        or os.getenv("VERCEL_URL")
        or os.getenv("VERCEL_REGION")
        or os.getenv("VERCEL_DEPLOYMENT_ID")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        or os.getenv("AWS_EXECUTION_ENV")
        or os.getenv("LAMBDA_TASK_ROOT")
        or os.getenv("RENDER")
        or os.getenv("DYNO")
        or os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("STREAMLIT_SHARING_MODE")
        or os.getenv("GENESIS_CLOUD_MODE") == "1"
        or os.path.exists("/mount/src")
    )


class SmartRouter:
    ROUTING_PROFILES = {
        "local_offline": {
            "name": "💻 Local Offline Brain (Ollama llama3.2:1b)",
            "description": "100% offline local AI running directly on Windows laptop hardware without internet",
            "chain": [
                ("ollama", "llama3.2:1b")
            ]
        },
        "speed": {
            "name": "⚡ Ultra-Fast Speed (<150ms)",
            "description": "Blazing fast inference via Gemini 3.5 Flash, OpenRouter Free & Pollinations",
            "chain": [
                ("gemini", "gemini-3.5-flash-lite"),
                ("gemini", "gemini-3.5-flash"),
                ("openrouter", "openrouter/free"),
                ("groq", "llama-3.3-70b-versatile"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        },
        "reasoning": {
            "name": "🧠 Deep Reasoning & Math",
            "description": "Complex chain-of-thought, mathematical proof, logic and deep planning",
            "chain": [
                ("gemini", "gemini-3.5-flash"),
                ("gemini", "gemini-3.8-flash"),
                ("openrouter", "openrouter/free"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        },
        "coding": {
            "name": "💻 Elite Software Architecture & Code",
            "description": "Complex full-stack coding with Claude Code, Cursor, FreeLLMAPI, OmniRoute & Gemini",
            "chain": [
                ("gemini", "gemini-3.5-flash"),
                ("gemini", "gemini-3.5-flash-lite"),
                ("openrouter", "openrouter/free"),
                ("freellmapi", "auto"),
                ("omniroute", "auto"),
                ("cerebras", "llama3.1-70b"),
                ("groq", "llama-3.3-70b-versatile"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        },
        "search": {
            "name": "🌐 Live Web Search & Grounding",
            "description": "Real-time web retrieval, current news, fact checking and source citations",
            "chain": [
                ("gemini", "gemini-3.5-flash"),
                ("openrouter", "openrouter/free"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        },
        "free_tier": {
            "name": "🆓 100% Zero-Cost / Free Tier (~11.7B Pool)",
            "description": "Auto-routes to verified 100% free models (Gemini, OpenRouter Free, FreeLLMAPI, OmniRoute, Pollinations)",
            "chain": [
                ("gemini", "gemini-3.5-flash"),
                ("gemini", "gemini-3.5-flash-lite"),
                ("openrouter", "openrouter/free"),
                ("freellmapi", "auto"),
                ("omniroute", "auto"),
                ("cerebras", "llama3.1-70b"),
                ("groq", "llama-3.3-70b-versatile"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        },
        "general": {
            "name": "⚖️ Balanced Frontier Intelligence",
            "description": "Optimal balance of quality, speed and conversational fluency",
            "chain": [
                ("gemini", "gemini-3.5-flash"),
                ("gemini", "gemini-3.5-flash-lite"),
                ("openrouter", "openrouter/free"),
                ("pollinations", "openai"),
                ("ollama", "llama3.2:1b")
            ]
        }
    }

    @classmethod
    def check_internet(cls) -> bool:
        """Fast non-blocking test to check if external internet is available."""
        if _is_cloud_env():
            return True
        for host, port in [("1.1.1.1", 443), ("1.1.1.1", 53), ("8.8.8.8", 443)]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((host, port))
                s.close()
                return True
            except Exception:
                continue
        return False

    @classmethod
    def classify_intent(cls, prompt: str) -> Tuple[str, float, str]:
        """
        Classifies user prompt intent into a routing profile:
        Returns: (profile_key, confidence_score, rationale)
        """
        text = prompt.lower().strip()

        # If user explicitly asks for offline / local
        if not _is_cloud_env() and any(k in text for k in ["offline", "local model", "run locally", "without internet", "ollama"]):
            return "local_offline", 0.99, "User requested local offline execution via Ollama."

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
        messages: List[Dict[str, Any]],
        profile_override: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
        api_key_override: Optional[str] = None,
        session_keys: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes smart routing with automatic multi-provider fallback waterfall.
        If offline: immediately locks to Local Ollama Brain without network timeouts.
        If online: routes to Frontier Cloud AI with instant fallback to Local Ollama.
        """
        is_cloud = _is_cloud_env()
        last_prompt = messages[-1].get("content", "") if messages else ""
        if profile_override and profile_override in cls.ROUTING_PROFILES:
            profile_key = profile_override
            rationale = f"Manual override: {cls.ROUTING_PROFILES[profile_key]['name']}"
            confidence = 1.0
        else:
            profile_key, confidence, rationale = cls.classify_intent(last_prompt)

        is_online = cls.check_internet()

        # Dual-Brain Auto-Decision:
        if not is_cloud and (not is_online or profile_key == "local_offline"):
            active_brain = "OFFLINE"
            chain = [("ollama", "llama3.2:1b")]
            rationale = "Operating in 100% Offline Mode on Windows Laptop (Ollama llama3.2:1b). Zero internet required."
            profile_name = "💻 Local Offline Brain"
            confidence = 1.0
        else:
            active_brain = "CLOUD" if is_cloud else "ONLINE"
            if is_cloud and profile_key == "local_offline":
                profile_key = "general"
            profile = cls.ROUTING_PROFILES[profile_key]
            base_chain = [pair for pair in profile["chain"] if not (is_cloud and pair[0] == "ollama")]
            s_keys = session_keys or {}
            # Dynamically prioritize any provider with an active API key ahead of keyless Pollinations
            configured_pairs: List[Tuple[str, str]] = []
            pollinations_pairs: List[Tuple[str, str]] = []
            unconfigured_pairs: List[Tuple[str, str]] = []
            seen_pids = set()

            def _has_active_key(pid_chk: str) -> bool:
                if pid_chk == "ollama":
                    return not is_cloud
                if pid_chk == "pollinations":
                    return True
                ev_chk = PROVIDERS_METADATA.get(pid_chk, {}).get("env_var")
                return bool(api_key_override or (ev_chk and (s_keys.get(ev_chk) or GatewayConfig.get_key(ev_chk))))

            for pid_b, mod_b in base_chain:
                seen_pids.add(pid_b)
                if pid_b == "pollinations":
                    pollinations_pairs.append((pid_b, mod_b))
                elif _has_active_key(pid_b):
                    configured_pairs.append((pid_b, mod_b))
                else:
                    unconfigured_pairs.append((pid_b, mod_b))

            for pid_k, meta_k in PROVIDERS_METADATA.items():
                if pid_k in seen_pids or pid_k in ("ollama", "pollinations"):
                    continue
                if _has_active_key(pid_k):
                    configured_pairs.append((pid_k, meta_k.get("default_model", "")))

            chain = configured_pairs + pollinations_pairs + unconfigured_pairs
            profile_name = profile["name"]

        # Yield routing metadata header
        yield {
            "meta_event": "routing_decision",
            "dual_brain_mode": active_brain,
            "profile": profile_key,
            "profile_name": profile_name,
            "rationale": rationale,
            "confidence": confidence,
            "chain": [{"provider": p, "model": m, "provider_name": PROVIDERS_METADATA.get(p, {}).get("name", p)} for p, m in chain]
        }

        # Try providers down the waterfall chain
        success = False
        attempted_providers = []
        tried_pollinations = False
        used_provider = "pollinations" if is_cloud else "ollama"
        used_model = "openai" if is_cloud else "llama3.2:1b"

        for provider_id, model in chain:
            if provider_id == "pollinations":
                tried_pollinations = True
            meta = PROVIDERS_METADATA.get(provider_id, {})
            attempted_providers.append(f"{meta.get('name', provider_id)} ({model})")

            yield {
                "meta_event": "attempting_provider",
                "dual_brain_mode": active_brain,
                "provider": provider_id,
                "provider_name": meta.get("name", provider_id),
                "model": model
            }

            got_content = False
            had_error = False

            try:
                async for chunk in UniversalAdapter.chat_stream(
                    provider_id=provider_id,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key_override=api_key_override,
                    session_keys=session_keys
                ):
                    if chunk.get("error") or chunk.get("status") == "missing_key":
                        had_error = True
                        yield {
                            "meta_event": "provider_fallback",
                            "failed_provider": meta.get("name", provider_id),
                            "reason": chunk.get("delta", "Provider unavailable")
                        }
                        break
                    else:
                        if chunk.get("delta"):
                            got_content = True
                        chunk["content"] = chunk.get("delta", "")
                        chunk["provider"] = provider_id
                        chunk["model"] = model
                        used_provider = provider_id
                        used_model = model
                        yield chunk
            except Exception as e:
                had_error = True
                yield {
                    "meta_event": "provider_fallback",
                    "failed_provider": meta.get("name", provider_id),
                    "reason": str(e)
                }

            if got_content and not had_error:
                success = True
                break

        if not success:
            last_prompt = messages[-1].get("content", "") if messages else "Hello"
            fallback_answer, fb_provider, fb_model = await asyncio.to_thread(
                cls.generate_uninterrupted_fallback_meta, last_prompt, tried_pollinations
            )
            words = fallback_answer.split(" ")
            for i, w in enumerate(words):
                chunk_text = w + (" " if i < len(words) - 1 else "")
                yield {
                    "delta": chunk_text,
                    "content": chunk_text,
                    "done": False,
                    "provider": fb_provider,
                    "model": fb_model
                }
            yield {
                "delta": "",
                "content": "",
                "done": True,
                "provider": fb_provider,
                "model": fb_model
            }

    @classmethod
    def _safe_eval_math(cls, prompt: str) -> Optional[str]:
        expr = re.sub(r"^(what is|calculate|compute|solve|evaluate|equals|=)\s+", "", prompt.strip(), flags=re.IGNORECASE)
        expr = expr.strip().rstrip("?.=").replace("^", "**")
        if not expr or not re.fullmatch(r"[\d\s+\-*/().%*,sqrtpicosinta]+", expr, flags=re.IGNORECASE):
            return None
        if not any(ch.isdigit() for ch in expr) or not any(op in expr for op in ("+", "-", "*", "/", "**", "%", "sqrt")):
            return None
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        funcs = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": math.pi}

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Name) and node.id.lower() in funcs and isinstance(funcs[node.id.lower()], float):
                return funcs[node.id.lower()]
            if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
                return ops[type(node.op)](_eval_node(node.operand))
            if isinstance(node, ast.BinOp) and type(node.op) in ops:
                if isinstance(node.op, ast.Pow):
                    exp_v = _eval_node(node.right)
                    if abs(exp_v) > 200:
                        raise ValueError("Exponent too large")
                return ops[type(node.op)](_eval_node(node.left), _eval_node(node.right))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                fn = funcs.get(node.func.id.lower())
                if callable(fn) and len(node.args) == 1:
                    return fn(_eval_node(node.args[0]))
            raise ValueError("Unsupported AST")

        try:
            res = _eval_node(ast.parse(expr, mode="eval"))
            if isinstance(res, float) and res.is_integer():
                res = int(res)
            elif isinstance(res, float):
                res = round(res, 6)
            return f"**Calculated Result:** `{expr}` = **{res}**"
        except Exception:
            return None

    @classmethod
    def _knowledge_synthesis_fallback(cls, prompt: str) -> Optional[str]:
        p = (prompt or "").strip()
        pl = p.lower()

        # 1. Conversational & Identity intents
        if re.fullmatch(r"(hi+|hello+|hey+|yo+|good morning|good evening|good afternoon|namaste|sup)[!. ]*", pl):
            return (
                "Hello! I am **GENESIS AI 5.0**, created by Ishit Jain. "
                'Ask me anything, enable **Web Search** / **Swarm** / **Image**, or present answers live on your **2.4" ESP32 Screen**!'
            )
        if re.fullmatch(r"(hi+|hello+|hey+)?\s*(how are you|how's it going|what's up|wassup)[?.! ]*", pl):
            return (
                "Running at peak cognitive telemetry! Ask any question, run Web Search / Swarm, "
                'or mirror responses live onto your **2.4" ESP32-C5 Screen**.'
            )
        if re.fullmatch(r"(thanks|thank you|thx|ok|okay|cool|nice|great|awesome)[!. ]*", pl):
            return 'You are welcome! Ask your next question anytime — chat and your **2.4" Screen** stay synced.'
        if re.search(r"(who are you|what is genesis|what can you do|who created you|who made you|who built you)", pl):
            return (
                "I am **GENESIS AI 5.0**, created by **Ishit Jain** — a multi-provider AI gateway unifying 22 model providers, "
                'live web grounding, 3-agent swarm debate, Flux.1 image generation, and real-time 2.4" ESP32-C5 TFT hardware sync.'
            )

        # 2. Safe Arithmetic
        math_ans = cls._safe_eval_math(p)
        if math_ans:
            return math_ans

        # 3. Clean query for Live Knowledge (handles conversational prefixes, question verbs & articles)
        clean = p
        # Strip trailing formatting constraints (e.g. "in 4 bullet points", "in 2 sentences", "step by step")
        clean = re.sub(
            r"\b(in\s+\d+\s+(crisp\s+|short\s+|brief\s+)?(bullet\s+points?|points?|sentences?|words?|lines?|paragraphs?)|in\s+detail|step\s+by\s+step|briefly|concisely|for\s+beginners?)\b.*$",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip()
        clean = re.sub(r"\b(works|work|overview|summary)\b$", "", clean, flags=re.IGNORECASE).strip()

        for _ in range(3):
            clean = re.sub(
                r"^(hi+|hello+|hey+|please|tell me|can you|could you|explain|what is|what are|what was|what were|who is|who are|who was|who were|define|how does|how do|how to|how can|how|describe)\b\s*",
                "",
                clean,
                flags=re.IGNORECASE,
            ).strip()
            clean = re.sub(
                r"^(who|what|where|when|which|why)\s+(is|are|was|were|built|created|made|invented|founded|designed|directed|wrote|discovered|painted|started|composed|leads|won|runs|did)\b\s*",
                "",
                clean,
                flags=re.IGNORECASE,
            ).strip()
            clean = re.sub(
                r"^(the\s+)?(builder|creator|maker|inventor|founder|designer|director|writer|author|discoverer|painter)\s+of\b\s*",
                "",
                clean,
                flags=re.IGNORECASE,
            ).strip()
            clean = re.sub(r"^(a|an|the|about|to me)\b\s*", "", clean, flags=re.IGNORECASE).strip()
        clean = clean.strip(" ?!.,:") or p

        headers = {"User-Agent": "OmniModelGateway/5.0 (https://github.com/ishitjainnimsuniversity-ai/OmniModel-AI-Gateway; contact: admin@omnimodel.internal)"}
        req_timeout = httpx.Timeout(5.0, connect=2.5)

        def _fetch_wiki_search() -> Tuple[str, str, str]:
            try:
                with httpx.Client(timeout=req_timeout, headers=headers, follow_redirects=True) as client:
                    rw = client.get(
                        "https://en.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "list": "search",
                            "srsearch": clean,
                            "srinfo": "suggestion",
                            "srprop": "snippet",
                            "srlimit": 5,
                            "format": "json",
                        },
                    )
                    if rw.status_code == 200:
                        qobj = rw.json().get("query", {})
                        hits = qobj.get("search") or []
                        sug = (qobj.get("searchinfo") or {}).get("suggestion")
                        if not hits and sug:
                            cand_sug = sug[0].upper() + sug[1:]
                            rs_sug = client.get(
                                f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(cand_sug.replace(' ', '_'))}"
                            )
                            if rs_sug.status_code == 200:
                                dsum = rs_sug.json()
                                ext = (dsum.get("extract") or "").strip()
                                url = dsum.get("content_urls", {}).get("desktop", {}).get("page", "")
                                if ext and dsum.get("type") != "disambiguation":
                                    return dsum.get("title") or cand_sug, ext, url
                            rw2 = client.get(
                                "https://en.wikipedia.org/w/api.php",
                                params={"action": "query", "list": "search", "srsearch": sug, "srprop": "snippet", "srlimit": 5, "format": "json"},
                            )
                            if rw2.status_code == 200:
                                hits = rw2.json().get("query", {}).get("search") or []
                        if hits:
                            # Re-rank hits to avoid tangential/mythical articles (e.g. "Black Taj Mahal") when searching for "Taj Mahal"
                            clean_lower = clean.lower()
                            clean_no_the = re.sub(r"^the\s+", "", clean_lower).strip()
                            best_hit = None
                            for h in hits:
                                h_title = (h.get("title") or "").strip().lower()
                                h_no_the = re.sub(r"^the\s+", "", h_title).strip()
                                if h_title == clean_lower or h_no_the == clean_no_the:
                                    best_hit = h
                                    break
                            if not best_hit:
                                for h in hits:
                                    h_title = (h.get("title") or "").strip().lower()
                                    if h_title.startswith(clean_lower) or clean_lower.startswith(h_title):
                                        best_hit = h
                                        break
                            if not best_hit:
                                best_hit = hits[0]

                            wtitle = best_hit.get("title", "")
                            rs = client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wtitle.replace(' ', '_'))}")
                            if rs.status_code == 200:
                                dsum = rs.json()
                                ext = (dsum.get("extract") or "").strip()
                                url = dsum.get("content_urls", {}).get("desktop", {}).get("page", "")
                                if ext:
                                    return wtitle, ext, url
                            snip = re.sub(r"<[^>]+>", "", best_hit.get("snippet") or "").strip()
                            if snip:
                                return wtitle, snip, f"https://en.wikipedia.org/wiki/{urllib.parse.quote(wtitle.replace(' ', '_'))}"
            except Exception:
                pass
            return "", "", ""

        def _fetch_wiki_direct_summary() -> Tuple[str, str, str]:
            # Direct REST v1 summary is fast (often <0.8s even if Action Search API stalls)
            candidates = []
            c_norm = re.sub(r"\s+", " ", clean).strip()
            if c_norm:
                candidates.append(c_norm[0].upper() + c_norm[1:])
                if c_norm.title() != candidates[0]:
                    candidates.append(c_norm.title())
            try:
                with httpx.Client(timeout=req_timeout, headers=headers, follow_redirects=True) as client:
                    for cand in candidates[:2]:
                        rs = client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(cand.replace(' ', '_'))}")
                        if rs.status_code == 200:
                            dsum = rs.json()
                            if dsum.get("type") == "disambiguation":
                                continue
                            ext = (dsum.get("extract") or "").strip()
                            url = dsum.get("content_urls", {}).get("desktop", {}).get("page", "")
                            if ext:
                                return dsum.get("title") or cand, ext, url
            except Exception:
                pass
            return "", "", ""

        def _fetch_ddg() -> List[str]:
            facts: List[str] = []
            try:
                with httpx.Client(timeout=req_timeout, headers=headers, follow_redirects=True) as client:
                    rd = client.get("https://api.duckduckgo.com/", params={"q": clean, "format": "json", "no_html": 1, "skip_disambig": 1})
                    if rd.status_code == 200:
                        dd = rd.json()
                        inst = (dd.get("Answer") or dd.get("AbstractText") or dd.get("Definition") or "").strip()
                        if inst:
                            facts.append(inst)
                        for rel in (dd.get("RelatedTopics") or [])[:2]:
                            if isinstance(rel, dict) and rel.get("Text"):
                                facts.append(rel["Text"][:220])
            except Exception:
                pass
            return facts

        wiki_title, wiki_extract, wiki_url = "", "", ""
        ddg_facts: List[str] = []
        pool = ThreadPoolExecutor(max_workers=3)
        try:
            f_search = pool.submit(_fetch_wiki_search)
            f_direct = pool.submit(_fetch_wiki_direct_summary)
            f_ddg = pool.submit(_fetch_ddg)

            done_futs, _ = cf_wait([f_search, f_direct, f_ddg], timeout=6.5)

            for fut in (f_search, f_direct):
                if fut in done_futs:
                    try:
                        wt, we, wu = fut.result()
                        if we and (fut is f_search or not wiki_extract):
                            wiki_title, wiki_extract, wiki_url = wt, we, wu
                    except Exception:
                        pass
            if f_ddg in done_futs:
                try:
                    raw_facts = f_ddg.result()
                    ddg_facts = [f for f in raw_facts if f and f not in wiki_extract]
                except Exception:
                    pass
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

        parts: List[str] = []
        if wiki_extract:
            header_title = f"### {wiki_title}" if wiki_title else "### Overview"
            parts.append(f"{header_title}\n\n{wiki_extract}")
        if ddg_facts:
            bullets = "\n".join(f"- {f}" for f in ddg_facts[:3])
            parts.append(f"**Key Highlights:**\n{bullets}")
        if wiki_url:
            parts.append(f"[Read full topic on Wikipedia]({wiki_url})")

        if parts:
            return "\n\n".join(parts)
        return None

    @classmethod
    def generate_uninterrupted_fallback_meta(cls, prompt: str, skip_pollinations: bool = False) -> Tuple[str, str, str]:
        """Returns (answer_text, provider_id, model_id) across Local Ollama, OpenRouter Free Pool, Pollinations, and Live Knowledge Engine."""
        # 1. Local Ollama first (skip inside cloud containers)
        if not _is_cloud_env():
            try:
                r = httpx.post(
                    "http://127.0.0.1:11434/v1/chat/completions",
                    json={"model": "llama3.2:1b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=httpx.Timeout(8.0, connect=0.6)
                )
                if r.status_code == 200:
                    ans = (r.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if ans:
                        return ans, "ollama", "llama3.2:1b"
            except Exception:
                pass

        # 2. OpenRouter Free Pool via Vault Key (Fast, high-fidelity frontier fallback without IP blocks)
        try:
            from core.vault import get_vault_key
            or_key = get_vault_key("OPENROUTER_API_KEY")
            if or_key:
                r_or = httpx.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                    json={
                        "model": "openrouter/free",
                        "messages": [
                            {"role": "system", "content": "You are GENESIS AI 5.0, created by Ishit Jain. Be strictly factual, direct, and concise."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 800
                    },
                    timeout=httpx.Timeout(9.0, connect=3.0)
                )
                if r_or.status_code == 200:
                    or_ans = (r_or.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if or_ans:
                        return or_ans, "openrouter", "openrouter/free"
        except Exception:
            pass

        # 2b. Google Gemini via Vault Key (Zero IP cooldown, sub-second latency)
        try:
            from core.vault import get_vault_key
            gem_key = get_vault_key("GEMINI_API_KEY")
            if gem_key:
                r_gem = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gem_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "systemInstruction": {"parts": [{"text": "You are GENESIS AI 5.0, created by Ishit Jain. Be strictly factual, direct, and concise."}]}
                    },
                    timeout=httpx.Timeout(9.0, connect=3.0)
                )
                if r_gem.status_code == 200:
                    g_data = r_gem.json()
                    cands = g_data.get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts).strip()
                        if text:
                            return text, "gemini", "gemini-3.5-flash"
        except Exception:
            pass

        # 3. Cloud fallback (Pollinations fast attempt if not already failed this turn)
        if not skip_pollinations:
            try:
                sys_ground = (
                    "You are GENESIS AI 5.0, created by Ishit Jain. "
                    "Be strictly factual, accurate, and concise. "
                    "Never invent facts, dates, citations, or formulas. "
                    "If you do not know something for certain, state that clearly."
                )
                r_post = httpx.post(
                    "https://text.pollinations.ai/openai",
                    json={
                        "model": "openai",
                        "messages": [
                            {"role": "system", "content": sys_ground},
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False
                    },
                    timeout=6.5
                )
                if r_post.status_code == 200:
                    ans = (r_post.json().get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
                    if ans and "Free limit reached" not in ans and "enter.pollinations.ai" not in ans:
                        return ans, "pollinations", "openai"
            except Exception:
                pass

        # 4. Live Knowledge, Spell-Corrected Summary & Math Synthesis
        synth = cls._knowledge_synthesis_fallback(prompt)
        if synth:
            return synth, "genesis-knowledge", "live-wiki-ddg"

        return (
            "⚡ **Keyless Cooldown Notice:** Free Pollinations inference is in its 45-second IP cooldown and no cloud API key "
            "(Gemini / OpenRouter / Groq) is currently configured in Secrets.\n\n"
            "- Wait ~45 seconds and resend your prompt, **or**\n"
            "- Add a free API key in **🌐 22 Providers Matrix** (or Streamlit **App Settings → Secrets**) for unlimited frontier AI.",
            "genesis-router",
            "keyless-guard",
        )

    @classmethod
    def generate_uninterrupted_fallback(cls, prompt: str) -> str:
        text, _, _ = cls.generate_uninterrupted_fallback_meta(prompt)
        return text
