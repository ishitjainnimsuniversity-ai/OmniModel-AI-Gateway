"""
OmniModel User Information, Activity & Telemetry Analytics Tracker
Tracks client IPs, user agents, models used, tokens, latency, and session activity.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
ANALYTICS_FILE = DATA_DIR / "analytics.json"

class AnalyticsTracker:
    _records: List[Dict[str, Any]] = []
    _max_records: int = 1000

    @classmethod
    def _load_records(cls):
        if not cls._records and ANALYTICS_FILE.exists():
            try:
                data = json.loads(ANALYTICS_FILE.read_text(encoding="utf-8"))
                cls._records = data.get("records", [])
            except Exception:
                cls._records = []

    @classmethod
    def _save_records(cls):
        try:
            payload = {
                "updated_at": datetime.utcnow().isoformat(),
                "total_records": len(cls._records),
                "records": cls._records[-cls._max_records:]
            }
            ANALYTICS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Error saving analytics: {e}")

    @classmethod
    def record_request(
        cls,
        client_ip: str,
        user_agent: str,
        endpoint: str,
        model: str,
        provider: str,
        latency_ms: float,
        status: str = "success",
        tokens_est: int = 0,
        prompt_snippet: str = ""
    ):
        cls._load_records()
        
        # Determine client platform / device
        ua_lower = user_agent.lower()
        platform = "Desktop / Web"
        if "python" in ua_lower or "httpx" in ua_lower or "requests" in ua_lower:
            platform = "Python SDK / Antigravity"
        elif "curl" in ua_lower:
            platform = "cURL Terminal"
        elif "node" in ua_lower or "axios" in ua_lower:
            platform = "Node.js / JS SDK"
        elif "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            platform = "Mobile Browser"

        record = {
            "id": f"req_{int(time.time()*1000)}_{len(cls._records)}",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "client_ip": client_ip or "127.0.0.1",
            "platform": platform,
            "user_agent": user_agent[:120] if user_agent else "Unknown",
            "endpoint": endpoint,
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 1),
            "status": status,
            "tokens_est": tokens_est,
            "snippet": prompt_snippet[:60] if prompt_snippet else ""
        }

        cls._records.append(record)
        if len(cls._records) > cls._max_records:
            cls._records.pop(0)

        cls._save_records()

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        cls._load_records()
        total_requests = len(cls._records)
        unique_ips = len(set(r.get("client_ip", "") for r in cls._records if r.get("client_ip")))
        total_tokens = sum(r.get("tokens_est", 0) for r in cls._records)
        avg_latency = round(sum(r.get("latency_ms", 0) for r in cls._records) / total_requests, 1) if total_requests else 0

        # Model distribution
        model_counts = Counter(r.get("model", "unknown") for r in cls._records)
        platform_counts = Counter(r.get("platform", "unknown") for r in cls._records)

        return {
            "total_requests": total_requests,
            "unique_users": unique_ips,
            "total_tokens": total_tokens,
            "avg_latency_ms": avg_latency,
            "top_models": dict(model_counts.most_common(5)),
            "top_platforms": dict(platform_counts.most_common(5)),
            "recent_activity": list(reversed(cls._records[-50:]))
        }

    @classmethod
    def clear_records(cls):
        cls._records = []
        cls._save_records()
