"""Live end-to-end tests against a RUNNING GENESIS AI backend (real cloud calls, nothing mocked).
Usage: python -m genesis_ai.tests.run_live_tests [base_url]
Writes genesis_ai/tests/last_results.json."""
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8100"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from genesis_ai.settings import settings  # noqa: E402

TOKEN = settings.access_token()
H = {"X-Genesis-Token": TOKEN}
results = []


def record(name, ok, detail="", secs=0.0):
    results.append({"test": name, "pass": bool(ok), "detail": detail[:220], "secs": round(secs, 1)})
    print(f"{'PASS' if ok else 'FAIL'}  {name:34s} {secs:5.1f}s  {detail[:150]}", flush=True)


async def chat(c, msg, cid=None, path="/api/chat", **extra):
    t = time.monotonic()
    r = await c.post(BASE + path, headers=H, json={"message": msg, "conversation_id": cid, **extra},
                     timeout=90)
    return r, time.monotonic() - t


async def main():
    async with httpx.AsyncClient() as c:
        # ---- health / auth
        r = await c.get(BASE + "/api/health?deep=1", timeout=20)
        j = r.json()
        record("health + deep cloud check", r.status_code == 200 and j.get("cloud_reachable") is True,
               f"ai_ready={j.get('ai_ready')} cloud={j.get('cloud_detail')}")
        r = await c.post(BASE + "/api/chat", json={"message": "hi"})
        record("auth: missing token rejected", r.status_code == 401, f"status={r.status_code}")
        r = await c.post(BASE + "/api/chat", headers={"X-Genesis-Token": "wrong"}, json={"message": "hi"})
        record("auth: wrong token rejected", r.status_code == 401, f"status={r.status_code}")

        # ---- empty / oversize
        r, dt = await chat(c, "   ")
        record("empty message -> 400", r.status_code == 400 and r.json()["error"]["code"] == "empty_message",
               r.text[:100], dt)
        r, dt = await chat(c, "x" * 4001)
        record("oversize message -> 413", r.status_code == 413, f"status={r.status_code}", dt)

        # ---- general + follow-up context
        r, dt = await chat(c, "Who invented the telephone?")
        j = r.json()
        cid = j.get("conversation_id")
        record("general question", r.status_code == 200 and "bell" in j.get("text", "").lower(),
               f"{j.get('provider')}/{j.get('model')}: {j.get('text','')[:80]!r}", dt)
        r, dt = await chat(c, "When was he born, and what else did he invent?", cid)
        j = r.json()
        ok = r.status_code == 200 and "1847" in j.get("text", "")
        record("follow-up uses context (pronoun 'he')", ok, j.get("text", "")[:110].replace("\n", " "), dt)
        other, dt = await chat(c, "When was he born?")
        jo = other.json()
        record("new conversation has NO stale context", other.status_code == 200 and "1847" not in jo.get("text", ""),
               jo.get("text", "")[:100].replace("\n", " "), dt)

        # ---- world knowledge / science / math
        r, dt = await chat(c, "What is the capital of Australia and roughly what is its population?")
        record("world knowledge", "canberra" in r.json().get("text", "").lower(), r.json().get("text", "")[:90], dt)
        r, dt = await chat(c, "Explain how photosynthesis works in 3 sentences.")
        record("science explanation", r.status_code == 200 and "light" in r.json().get("text", "").lower(), "", dt)
        r, dt = await chat(c, "Calculate 48 * 25 + 120 and show the steps.")
        record("mathematics", "1320" in r.json().get("text", "").replace(",", ""), r.json().get("text", "")[:80].replace("\n", " "), dt)

        # ---- writing / code
        r, dt = await chat(c, "Write a professional email to my manager asking for Friday off. Keep it short.")
        t = r.json().get("text", "")
        record("write email", r.status_code == 200 and "subject" in t.lower() and len(t) > 120, f"{len(t)} chars", dt)
        r, dt = await chat(c, "Write a 400-word essay on the importance of renewable energy.")
        t = r.json().get("text", "")
        words = len(t.split())
        record("write long essay (~400 words)", r.status_code == 200 and words >= 300, f"{words} words", dt)
        r, dt = await chat(c, "Write a Python function that reverses a string. Code only.")
        t = r.json().get("text", "")
        record("generate python code", "def " in t and "return" in t, t[:80].replace("\n", " "), dt)
        r, dt = await chat(c, "Debug this: def avg(xs): return sum(xs)/len(xs)\nprint(avg([]))")
        t = r.json().get("text", "").lower()
        record("debug code", "zero" in t or "empty" in t, t[:100].replace("\n", " "), dt)

        # ---- honesty on live data (no search tool yet -> must not fabricate)
        r, dt = await chat(c, "What is the current Bitcoin price right now in USD?")
        t = r.json().get("text", "")
        fabricated = bool(re.search(r"\$\s?\d{2,3},\d{3}", t)) and not re.search(r"cannot|can't|unable|don't have|do not have|no (live|real)", t.lower())
        record("does not fabricate live data", r.status_code == 200 and not fabricated, t[:140].replace("\n", " "), dt)

        # ---- repeated requests give independent answers
        a, _ = await chat(c, "Reply with only the word: ALPHA")
        b, _ = await chat(c, "Reply with only the word: BRAVO")
        ta, tb = a.json().get("text", ""), b.json().get("text", "")
        record("repeated requests not stale", "alpha" in ta.lower() and "bravo" in tb.lower() and "alpha" not in tb.lower(), f"{ta!r} / {tb!r}")

        # ---- concurrency: 6 parallel, different conversations
        t0 = time.monotonic()
        qs = [f"Reply with only the number {n}*{n}" for n in (3, 4, 5, 6, 7, 8)]
        rs = await asyncio.gather(*[chat(c, q) for q in qs])
        exp = ["9", "16", "25", "36", "49", "64"]
        ok = all(r.status_code == 200 and e in r.json().get("text", "") for (r, _), e in zip(rs, exp))
        ids = {r.json().get("request_id") for r, _ in rs}
        record("6 concurrent requests isolated", ok and len(ids) == 6, f"unique ids={len(ids)}", time.monotonic() - t0)

        # ---- streaming
        t = time.monotonic()
        parts, done = [], None
        async with c.stream("POST", BASE + "/api/chat/stream", headers=H, json={"message": "Count from 1 to 5, comma separated."}, timeout=90) as s:
            async for line in s.aiter_lines():
                if line.startswith("data:"):
                    ev = json.loads(line[5:])
                    if ev["type"] == "delta":
                        parts.append(ev["text"])
                    if ev["type"] == "done":
                        done = ev
        record("streaming SSE", done is not None and "5" in "".join(parts) and len(parts) >= 1, f"{len(parts)} chunks", time.monotonic() - t)

        # ---- device API + pagination
        r, dt = await chat(c, "Write a 200-word explanation of how the internet works.", path="/api/device/chat", cols=26, rows=8)
        j = r.json()
        ok = r.status_code == 200 and j.get("total_pages", 0) >= 3 and all(len(l) <= 26 for l in j["text"].split("\n"))
        record("device chat paginates 26x8", ok, f"pages={j.get('total_pages')} chars={j.get('chars')}", dt)
        if j.get("request_id"):
            p2 = (await c.get(BASE + "/api/device/page", headers=H, params={"request_id": j["request_id"], "page": 1})).json()
            record("device page fetch", p2.get("page") == 1 and p2.get("text"), p2.get("text", "")[:60].replace("\n", " | "))
        txt = j.get("text", "")
        record("device text is plain ASCII", all(ord(ch) < 128 for ch in txt) and "**" not in txt and "#" not in txt, "")

        # ---- conversation management
        cc = (await c.post(BASE + "/api/conversations", headers=H)).json()["id"]
        await chat(c, "Remember the word PINEAPPLE.", cc)
        rr, _ = await chat(c, "What word did I ask you to remember?", cc)
        remembered = "pineapple" in rr.json().get("text", "").lower()
        await c.post(BASE + f"/api/conversations/{cc}/clear", headers=H)
        rr2, _ = await chat(c, "What word did I ask you to remember?", cc)
        forgot = "pineapple" not in rr2.json().get("text", "").lower()
        record("memory then clear conversation", remembered and forgot, f"remembered={remembered} forgot_after_clear={forgot}")

    # ---- in-process failure-mode tests (explicitly simulated)
    from genesis_ai.service import ChatService, ChatError
    from genesis_ai.conversations import ConversationStore
    import os
    svc = ChatService(ConversationStore(persist=False))

    saved = os.environ.get("GEMINI_API_KEY")
    from genesis_ai import settings as S
    # invalid credentials (SIMULATED by pointing the process at a bad key; .env is untouched)
    S.get_secret.__globals__["reload_env"] = lambda: None
    os.environ["GEMINI_API_KEY"] = "AQ.invalid-key-for-testing"
    try:
        await svc.chat("hello")
        record("invalid API key -> clear error", False, "no error raised")
    except ChatError as e:
        record("invalid API key -> clear error", e.attempts and e.attempts[-1]["code"] in ("auth_failed", "bad_request"), f"{e.attempts[-1]['code']}: {e.message}")
    finally:
        os.environ["GEMINI_API_KEY"] = saved or ""

    # internet disconnection (SIMULATED: unreachable endpoint)
    prov = svc.registry["gemini"]
    old_base = prov.base
    prov.base = "https://127.0.0.1:9/v1beta"
    try:
        await svc.chat("hello")
        record("network down -> clear error", False, "no error raised")
    except ChatError as e:
        record("network down -> clear error", e.attempts and e.attempts[-1]["code"] in ("network_error", "timeout"), f"{e.attempts[-1]['code']}: {e.message}")
    finally:
        prov.base = old_base

    # rate limit (REAL: OpenRouter free quota is exhausted right now) with only that provider
    os.environ["GENESIS_PROVIDER"] = "openrouter"
    try:
        await svc.chat("hello")
        record("rate limit -> clear error (real 429)", False, "no error raised")
    except ChatError as e:
        record("rate limit -> clear error (real 429)", e.attempts and e.attempts[-1]["code"] == "rate_limited", f"{e.attempts[-1]['code']}: {e.message}")
    finally:
        os.environ["GENESIS_PROVIDER"] = "gemini"

    # fallback only when configured: primary broken + openrouter listed but rate limited => reports failure, never fabricates
    os.environ["GENESIS_FALLBACKS"] = "openai"
    try:
        os.environ["GEMINI_API_KEY"] = "AQ.invalid-key-for-testing"
        await svc.chat("hello")
        record("unconfigured fallback is skipped, no fake answer", False, "no error raised")
    except ChatError as e:
        codes = [a["code"] for a in e.attempts]
        record("unconfigured fallback is skipped, no fake answer", "not_configured" in codes and e.code == "all_providers_failed", str(codes))
    finally:
        os.environ["GEMINI_API_KEY"] = saved or ""
        os.environ["GENESIS_FALLBACKS"] = ""

    p = sum(r["pass"] for r in results)
    print(f"\n{p}/{len(results)} passed")
    Path(__file__).with_name("last_results.json").write_text(json.dumps(results, indent=1))


asyncio.run(main())
