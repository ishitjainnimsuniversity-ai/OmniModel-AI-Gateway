"""
GENESIS AI 5.0 — Worldwide Cloud-to-2.4"-ESP32 Screen Relay Agent
Run on any laptop / Raspberry Pi / Termux phone on the same Wi-Fi/hotspot as your ESP32-C5.
Polls your cloud gateway (/api/screen/poll) and mirrors text, GPIO27 RGB brightness,
page/clear actions, and RGB565 Image Studio frames to the ESP32-C5 in real time!

Usage:
    python cloud_to_esp32_sync.py
    python cloud_to_esp32_sync.py --relay https://omni-model-ai-gateway.vercel.app --esp-ip 10.33.110.73
"""

import argparse
import os
import sys
import time
import urllib.request
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.screen_bridge import HardwareScreenBridge  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="GENESIS AI 5.0 Cloud -> ESP32-C5 2.4-inch Screen Relay")
    parser.add_argument(
        "--relay",
        default=os.getenv("GENESIS_CLOUD_RELAY", "https://omni-model-ai-gateway.vercel.app"),
        help="Cloud Gateway base URL exposing /api/screen/poll",
    )
    parser.add_argument(
        "--esp-ip",
        default=os.getenv("ESP32_WIFI_IP", "10.33.110.73"),
        help="Direct ESP32-C5 Wi-Fi IP (fallback scans subnet and 192.168.4.1)",
    )
    parser.add_argument(
        "--port",
        default=r"\\.\COM4" if sys.platform == "win32" else "/dev/ttyACM0",
        help="USB Serial port for ESP32-C5 when wired",
    )
    parser.add_argument("--interval", type=float, default=1.5, help="Poll interval in seconds")
    args = parser.parse_args()

    bridge = HardwareScreenBridge(port=args.port, default_ip=args.esp_ip)
    bridge.cloud_mode = False
    bridge.start_background_tasks()

    relay_base = args.relay.rstrip("/")
    print("=" * 68)
    print("GENESIS AI 5.0 // Cloud -> 2.4\" ESP32-C5 Hardware Sync Agent")
    print(f"Cloud Relay : {relay_base}")
    print(f"Target ESP  : {args.esp_ip} (+ SoftAP 192.168.4.1 + USB {args.port})")
    print("=" * 68)

    last_version = 0
    seen_cmd_ids = set()

    while True:
        try:
            url = f"{relay_base}/api/screen/poll?v={last_version}"
            req = urllib.request.Request(url, headers={"User-Agent": "GenesisSyncAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("changed"):
                        last_version = data.get("version", last_version)
                        cid = data.get("cmd_id", "")
                        if cid and cid != "init" and cid not in seen_cmd_ids:
                            seen_cmd_ids.add(cid)
                            if len(seen_cmd_ids) > 200:
                                seen_cmd_ids.clear()
                            payload = data.get("command_payload") or {}
                            cmd_obj = {
                                "action": data.get("action", "feed"),
                                "cmd_id": cid,
                                "state": data.get("state", "ANSWERED"),
                                "question": data.get("question", ""),
                                "text": data.get("text", ""),
                                "provider": data.get("provider", "Gemini"),
                                "model": data.get("model", "GENESIS AI 5.0"),
                                "brightness": data.get("brightness", payload.get("brightness", 45)),
                                **payload,
                            }
                            res = bridge.execute_command(cmd_obj)
                            print(
                                f"[Sync] Applied {cmd_obj['action']} (v={last_version}, state={cmd_obj['state']}): "
                                f"ok={res.get('ok')} wifi={bridge._wifi_ok}",
                                flush=True,
                            )
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print(f"[Sync] Poll retry ({exc})", flush=True)
        time.sleep(max(0.6, args.interval))


if __name__ == "__main__":
    main()
