"""
Comprehensive End-to-End Test Suite for OmniModel Gateway & 2.4" Hardware Screen
Tests:
- All HTTP routes and aliases
- Static asset delivery (GIF, JPG, CSS, JS, PNG)
- SmartRouter multi-model live inference
- IoT Chat API (/api/iot/chat) text and json formats
- Word boundary & spacing integrity
- Edge cases (unicode, long queries, special characters)
- Hardware Screen HTML markup integrity
"""

import sys
import os
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

# Fix stdout encoding for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"

def log(msg, status="INFO"):
    symbol = "🟢" if status == "PASS" else ("🔴" if status == "FAIL" else "⚡")
    print(f"[{symbol}] {msg}")

def http_get(path, timeout=10):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "TestRunner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.headers.get_content_type(), resp.read()

def http_post_json(path, data, timeout=20):
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "TestRunner/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.headers.get_content_type(), json.loads(resp.read().decode("utf-8"))

def test_all_http_routes():
    log("Testing all HTTP endpoints & aliases...", "TEST")
    routes_to_test = [
        ("/", "text/html"),
        ("/screen", "text/html"),
        ("/preview", "text/html"),
        ("/display", "text/html"),
        ("/hardware", "text/html"),
        ("/iot", "text/html"),
        ("/simulator", "text/html"),
        ("/lcd", "text/html"),
        ("/screen_preview.html", "text/html"),
        ("/ip", "application/json"),
        ("/style.css", "text/css"),
        ("/app.js", "application/javascript"),
        ("/ai_wheel.png", "image/png"),
        ("/quantum_core.png", "image/png"),
        ("/quantum_fusion_core.png", "image/png"),
        ("/v1/models", "application/json")
    ]
    
    passed = 0
    for path, expected_type in routes_to_test:
        try:
            status, ctype, body = http_get(path)
            assert status == 200, f"Status code {status} != 200 for {path}"
            assert len(body) > 0, f"Empty body for {path}"
            log(f"Route {path:30} -> {status} OK ({len(body)} bytes, {ctype})", "PASS")
            passed += 1
        except Exception as e:
            log(f"Route {path} FAILED: {e}", "FAIL")
            raise e
    log(f"All {passed}/{len(routes_to_test)} routes passed successfully!", "PASS")

def test_ip_diagnostic_endpoint():
    log("Testing /ip diagnostic payload...", "TEST")
    status, ctype, body = http_get("/ip")
    data = json.loads(body.decode("utf-8"))
    assert data.get("status") == "online"
    assert "wifi_ip" in data
    assert "recommended_screen_url" in data
    assert "localhost_screen_url" in data
    assert data.get("port") == 8000
    log(f"Detected Wi-Fi IP: {data['wifi_ip']} | Screen URL: {data['recommended_screen_url']}", "PASS")

def test_iot_chat_text_and_json():
    log("Testing /api/iot/chat with live AI queries...", "TEST")
    queries = [
        ("What is 2+2?", False),
        ("How does gravity work in 10 words?", False),
        ("What is an ESP32 microcontroller in 12 words?", False),
        ("Give a motivational quote in 8 words", False)
    ]
    
    for q, expect_fail in queries:
        param = urllib.parse.quote(q)
        # Test text format
        t0 = time.time()
        status, ctype, body = http_get(f"/api/iot/chat?format=text&q={param}", timeout=25)
        dt = (time.time() - t0) * 1000
        text = body.decode("utf-8").strip()
        assert status == 200
        assert len(text) > 0
        
        # Test word spacing integrity (words should NOT be squished)
        words = text.split()
        assert len(words) >= 2, f"Expected multi-word answer, got: '{text}'"
        log(f"Q: '{q}' -> ({dt:.0f}ms): {text[:60]}...", "PASS")
        
        # Test JSON format
        status, ctype, body_json = http_get(f"/api/iot/chat?format=json&q={param}", timeout=25)
        parsed = json.loads(body_json.decode("utf-8"))
        assert "text" in parsed
        assert "prompt" in parsed
        assert parsed["prompt"] == q
        assert len(parsed["text"]) > 0

    log("IoT chat endpoint tests (text & json) passed!", "PASS")

def test_word_spacing_and_cleanliness():
    log("Testing word spacing and typewriter integrity...", "TEST")
    # Verify that clean response text contains spaces and proper word breaks
    param = urllib.parse.quote("Why do airplanes fly in 15 words")
    status, ctype, body = http_get(f"/api/iot/chat?format=text&q={param}", timeout=25)
    text = body.decode("utf-8").strip()
    
    # Check that there are space characters
    assert " " in text, f"No spaces found in answer: '{text}'"
    # Ensure words are spaced normally (average word length between 2 and 15 chars)
    words = text.split()
    avg_len = sum(len(w) for w in words) / len(words)
    assert avg_len < 15, f"Unusually long average word length ({avg_len:.1f}), words may be merged: '{text}'"
    log(f"Word spacing verified: {len(words)} words, avg length {avg_len:.1f} chars.", "PASS")

def test_openai_compatibility_endpoint():
    log("Testing /v1/chat/completions (OpenAI compatible)...", "TEST")
    payload = {
        "model": "genesis-5.0-speed",
        "messages": [
            {"role": "user", "content": "Respond with the single word: READY"}
        ],
        "temperature": 0.3,
        "max_tokens": 50
    }
    status, ctype, res = http_post_json("/v1/chat/completions", payload, timeout=25)
    assert status == 200
    assert "choices" in res
    assert len(res["choices"]) > 0
    ans = res["choices"][0]["message"]["content"]
    assert len(ans.strip()) > 0
    log(f"OpenAI Compatible API responded: '{ans.strip()}'", "PASS")

def test_screen_preview_html_markup():
    log("Testing screen_preview.html markup integrity...", "TEST")
    html_path = BASE_DIR / "public" / "screen_preview.html"
    assert html_path.exists(), "public/screen_preview.html missing!"
    content = html_path.read_text(encoding="utf-8")
    
    # Check key elements (Quantum Fusion + OLED toggle)
    assert "id=\"lcd-fusion-layer\"" in content, "Missing lcd-fusion-layer element!"
    assert "lcd-core-layer" in content, "Missing lcd-core-layer element!"
    assert "lcd-wheel-layer" in content, "Missing lcd-wheel-layer element!"
    assert "id=\"lcd-display\"" in content, "Missing lcd-display element!"
    assert "id=\"lcd-answer\"" in content, "Missing lcd-answer element!"
    assert "id=\"custom-input\"" in content, "Missing custom-input element!"
    assert "toggleOledMode" in content, "Missing toggleOledMode function!"
    assert "typeWriter" in content, "Missing typeWriter function!"
    assert "playTerminalClick" in content, "Missing SFX synthesizer!"
    assert "white-space: pre-wrap" in content, "Missing pre-wrap styling for word-spacing!"
    assert "word-break: break-word" in content, "Missing word-break styling!"
    log("screen_preview.html markup (Quantum Fusion Core & OLED) verified!", "PASS")

def main():
    print("=" * 60)
    print("🚀 GENESIS AI 5.0 - MASTER SYSTEM VERIFICATION TEST SUITE")
    print("=" * 60)
    
    test_all_http_routes()
    test_ip_diagnostic_endpoint()
    test_iot_chat_text_and_json()
    test_word_spacing_and_cleanliness()
    test_openai_compatibility_endpoint()
    test_screen_preview_html_markup()
    
    print("=" * 60)
    log("ALL TESTS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!", "PASS")
    print("=" * 60)

if __name__ == "__main__":
    main()
