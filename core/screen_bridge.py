"""
Universal Screen Bridge for ESP32-C5 2.4-inch ILI9341 Screen
Supports DUAL HYBRID OPERATION:
1. Wi-Fi Network Synchronization (HTTP REST) - works anywhere in the room, on wall charger or battery.
2. USB Serial Synchronization (CDC COM4) - works with ultra-low latency when plugged into the laptop.
"""

from collections import deque
import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request

try:
    import serial
except ImportError:
    serial = None

IS_CLOUD_RUNTIME = bool(
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


class HardwareScreenBridge:
    def __init__(self, port=r"\\.\COM4", baud=115200, default_ip="10.33.110.73"):
        self.port = port
        self.baud = baud
        self.ser = None
        self._lock = threading.Lock()
        self._last_sent_state = ""
        self._last_sent_time = 0.0
        self.cloud_mode = IS_CLOUD_RUNTIME
        self._workers_started = False

        # Global Feed Cache for Worldwide Polling & Cloud Command Relay
        self.latest_feed = {
            "version": 1,
            "cmd_id": "init",
            "action": "feed",
            "state": "READY",
            "question": "",
            "text": "",
            "provider": "Gemini",
            "model": "GENESIS AI 5.0",
            "brightness": 45,
            "command_payload": {},
            "timestamp": time.time()
        }

        # Wi-Fi Sync State
        self.esp_wifi_ip = "" if self.cloud_mode else default_ip
        self._wifi_ok = False
        self._last_scan_time = 0.0
        self._rgb_brightness = 45
        self._seen_cmd_ids = deque(maxlen=128)
        self._cloud_poller_started = False

    def start_background_tasks(self):
        """Starts local USB serial and Wi-Fi LAN monitor threads (skipped in cloud)."""
        if self.cloud_mode or self._workers_started:
            return
        self._workers_started = True
        self._connect_usb()
        self._start_usb_reader()
        self._start_wifi_monitor()

    def _connect_usb(self):
        if serial is None or self.cloud_mode:
            self.ser = None
            return False
        try:
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
            s = serial.Serial()
            s.port = self.port
            s.baudrate = self.baud
            s.timeout = 0.2
            s.dtr = False
            s.rts = False
            s.open()
            self.ser = s
            print(f"[ScreenBridge] Connected to ESP32-C5 on USB {self.port} (DTR/RTS protected)", flush=True)
            return True
        except Exception:
            self.ser = None
            return False

    def _start_usb_reader(self):
        def reader_loop():
            while True:
                try:
                    with self._lock:
                        if self.ser and self.ser.is_open:
                            waiting = self.ser.in_waiting
                            if waiting > 0:
                                data = self.ser.read(waiting)
                                if data:
                                    text = data.decode("utf-8", errors="replace").strip()
                                    if text:
                                        print(f"[ESP32-Log] {text}", flush=True)
                                        # Parse STA IP from boot logs if available
                                        if "CONNECTED TO HOTSPOT! IP:" in text:
                                            m = re.search(r"IP:\s*([\d\.]+)", text)
                                            if m:
                                                new_ip = m.group(1).strip()
                                                self.esp_wifi_ip = new_ip
                                                print(f"[ScreenBridge] Auto-discovered ESP32 IP from Serial: {new_ip}", flush=True)
                except Exception:
                    pass
                time.sleep(0.05)

        t = threading.Thread(target=reader_loop, daemon=True)
        t.start()

    def _get_local_ip_subnets(self):
        subnets = set()
        try:
            # Check host IPs
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    parts = ip.split(".")
                    if len(parts) == 4:
                        subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}.")
        except Exception:
            pass
        # Always include common hotspot subnets
        subnets.add("10.33.110.")
        subnets.add("192.168.43.")
        subnets.add("192.168.4.")
        return list(subnets)

    def _probe_ip(self, ip: str) -> bool:
        try:
            url = f"http://{ip}/api/status"
            req = urllib.request.Request(url, headers={"User-Agent": "GenesisBridge/1.0"})
            with urllib.request.urlopen(req, timeout=0.6) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode("utf-8"))
                    if data.get("device") == "ESP32-C5":
                        return True
        except Exception:
            pass
        return False

    def scan_subnet(self):
        # 1. Quick check current known IP
        if self.esp_wifi_ip and self._probe_ip(self.esp_wifi_ip):
            self._wifi_ok = True
            return self.esp_wifi_ip

        # 2. Check 192.168.4.1 (SoftAP default)
        if self._probe_ip("192.168.4.1"):
            self.esp_wifi_ip = "192.168.4.1"
            self._wifi_ok = True
            return self.esp_wifi_ip

        # 3. Fast concurrent scan across active subnets
        subnets = self._get_local_ip_subnets()
        found_ip = None

        def worker(target_ip):
            nonlocal found_ip
            if found_ip:
                return
            if self._probe_ip(target_ip):
                found_ip = target_ip

        threads = []
        for subnet in subnets:
            for i in range(1, 255):
                ip = f"{subnet}{i}"
                t = threading.Thread(target=worker, args=(ip,), daemon=True)
                threads.append(t)
                t.start()
                if len(threads) >= 60:
                    for th in threads:
                        th.join(timeout=0.65)
                    threads = []
                if found_ip:
                    break
            if found_ip:
                break

        for th in threads:
            th.join(timeout=0.65)

        if found_ip:
            self.esp_wifi_ip = found_ip
            self._wifi_ok = True
            print(f"[ScreenBridge] Auto-discovered ESP32-C5 on Wi-Fi at: {found_ip}", flush=True)
            return found_ip
        else:
            self._wifi_ok = False
            return None

    def _start_wifi_monitor(self):
        def monitor_loop():
            # Initial probe
            self.scan_subnet()
            while True:
                time.sleep(12)
                try:
                    if self.esp_wifi_ip:
                        self._wifi_ok = self._probe_ip(self.esp_wifi_ip)
                    if not self._wifi_ok:
                        self.scan_subnet()
                except Exception:
                    pass

        t = threading.Thread(target=monitor_loop, daemon=True)
        t.start()

    @property
    def is_connected(self) -> bool:
        return (self.ser is not None and self.ser.is_open) or self._wifi_ok

    def set_target_ip(self, ip: str) -> bool:
        clean_ip = (ip or "").strip().replace("http://", "").replace("https://", "").rstrip("/")
        if not clean_ip:
            return False
        self.esp_wifi_ip = clean_ip
        if not self.cloud_mode:
            self._wifi_ok = self._probe_ip(clean_ip)
        return self._wifi_ok

    def query_esp32_status(self, target_ip: str = "") -> dict:
        if self.cloud_mode:
            return {"reachable": False, "cloud_mode": True}
        candidates = []
        if target_ip:
            candidates.append(target_ip.strip().replace("http://", "").rstrip("/"))
        if self.esp_wifi_ip and self.esp_wifi_ip not in candidates:
            candidates.append(self.esp_wifi_ip)
        if "192.168.4.1" not in candidates:
            candidates.append("192.168.4.1")

        for ip in candidates:
            try:
                req = urllib.request.Request(f"http://{ip}/api/status", headers={"User-Agent": "GenesisBridge/2.0"})
                with urllib.request.urlopen(req, timeout=1.0) as r:
                    if r.status == 200:
                        data = json.loads(r.read().decode("utf-8"))
                        self.esp_wifi_ip = ip
                        self._wifi_ok = True
                        try:
                            rgb_req = urllib.request.Request(f"http://{ip}/api/rgb", headers={"User-Agent": "GenesisBridge/2.0"})
                            with urllib.request.urlopen(rgb_req, timeout=0.8) as rr:
                                if rr.status == 200:
                                    rgb_data = json.loads(rr.read().decode("utf-8"))
                                    if "brightness" in rgb_data:
                                        self._rgb_brightness = int(rgb_data["brightness"])
                        except Exception:
                            pass
                        data["reachable"] = True
                        data["target_ip"] = ip
                        data["rgb_brightness"] = self._rgb_brightness
                        return data
            except Exception:
                continue
        return {"reachable": False, "usb_connected": bool(self.ser and self.ser.is_open), "last_ip": self.esp_wifi_ip}

    def get_status(self) -> dict:
        return {
            "cloud_mode": self.cloud_mode,
            "usb_connected": bool(self.ser and self.ser.is_open),
            "wifi_ip": self.esp_wifi_ip,
            "wifi_connected": self._wifi_ok,
            "rgb_brightness": self._rgb_brightness,
            "feed_version": self.latest_feed.get("version", 1),
            "last_synced_state": self._last_sent_state,
            "last_synced_time": self._last_sent_time
        }

    def _sanitize_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<thought>[\s\S]*?</thought>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"###+\s*", "", text)
        text = re.sub(r"`{1,3}", "", text)
        text = text.strip()
        if len(text) > 1200:
            text = text[:1197] + "..."
        return text

    def _push_wifi_async(self, ip: str, payload: dict):
        def _post():
            try:
                url = f"http://{ip}/api/feed"
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json", "User-Agent": "GenesisBridge/2.0"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as r:
                    if r.status == 200:
                        self._wifi_ok = True
            except Exception:
                pass

        threading.Thread(target=_post, daemon=True).start()

    def send_feed(self, state: str, question: str, provider: str, model: str, text: str = "", cmd_id: str = ""):
        now = time.time()
        # Debounce duplicate identical states within 0.8 seconds
        if state == "ANSWERED" and self._last_sent_state == "ANSWERED" and (now - self._last_sent_time) < 0.8:
            return True

        clean_ans = self._sanitize_text(text)
        self.latest_feed["version"] = self.latest_feed.get("version", 0) + 1
        self.latest_feed["action"] = "feed"
        self.latest_feed["cmd_id"] = cmd_id or f"feed_{int(now * 1000)}_{self.latest_feed['version']}"
        self.latest_feed["command_payload"] = {}
        self.latest_feed["state"] = state
        self.latest_feed["question"] = question[:250].strip()
        self.latest_feed["provider"] = provider[:20]
        self.latest_feed["model"] = model[:25]
        self.latest_feed["text"] = clean_ans
        self.latest_feed["timestamp"] = time.time()

        payload = {
            "state": state,
            "question": question[:250].strip(),
            "provider": provider[:20],
            "model": model[:25],
            "text": clean_ans
        }

        if self.cloud_mode:
            self._last_sent_state = state
            self._last_sent_time = time.time()
            return True

        success = False

        # Channel 1: Wi-Fi Sync (Works on wall charger & anywhere in the room)
        if self.esp_wifi_ip:
            self._push_wifi_async(self.esp_wifi_ip, payload)
            success = True
            print(f"[ScreenBridge] Pushed update via Wi-Fi ({self.esp_wifi_ip}): state={state}, q='{question[:30]}'", flush=True)

        # Also push to 192.168.4.1 if different from current wifi IP
        if self.esp_wifi_ip != "192.168.4.1":
            self._push_wifi_async("192.168.4.1", payload)

        # Channel 2: USB Serial Sync (if plugged into laptop)
        with self._lock:
            if self.ser and self.ser.is_open:
                try:
                    line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
                    chunk_size = 64
                    for idx in range(0, len(line), chunk_size):
                        chunk = line[idx:idx + chunk_size]
                        self.ser.write(chunk)
                        self.ser.flush()
                        time.sleep(0.004)
                    success = True
                except Exception:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None

        self._last_sent_state = state
        self._last_sent_time = time.time()
        return success

    def send_thinking(self, question: str, provider: str = "Gemini", model: str = ""):
        disp_provider = provider
        if disp_provider in ("router", "relay", "gateway", ""):
            disp_provider = "Gemini"
        return self.send_feed("THINKING", question, disp_provider, model, "")

    def send_answer(self, question: str, text: str, provider: str = "Gemini", model: str = ""):
        disp_provider = provider
        if disp_provider in ("router", "relay", "gateway", ""):
            disp_provider = "Gemini"
        return self.send_feed("ANSWERED", question, disp_provider, model, text)

    def _candidate_ips(self, target_ip: str = "") -> list:
        ips = []
        if target_ip:
            clean = target_ip.strip().replace("http://", "").replace("https://", "").rstrip("/")
            if clean:
                ips.append(clean)
        if self.esp_wifi_ip and self.esp_wifi_ip not in ips:
            ips.append(self.esp_wifi_ip)
        if "192.168.4.1" not in ips:
            ips.append("192.168.4.1")
        return ips

    def _post_esp_endpoint(self, path: str, body: dict = None, target_ip: str = "", timeout: float = 2.0) -> bool:
        if self.cloud_mode:
            return False
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b"{}"
        headers = {"Content-Type": "application/json", "User-Agent": "GenesisBridge/2.0"}
        for ip in self._candidate_ips(target_ip):
            try:
                req = urllib.request.Request(f"http://{ip}{path}", data=raw, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    if r.status == 200:
                        self.esp_wifi_ip = ip
                        self._wifi_ok = True
                        return True
            except Exception:
                continue
        return False

    def _bump_feed_command(self, action: str, command_payload: dict = None, cmd_id: str = ""):
        cid = cmd_id or f"{action}_{int(time.time() * 1000)}"
        self._seen_cmd_ids.append(cid)
        self.latest_feed["version"] = self.latest_feed.get("version", 0) + 1
        self.latest_feed["cmd_id"] = cid
        self.latest_feed["action"] = action
        self.latest_feed["command_payload"] = command_payload or {}
        self.latest_feed["timestamp"] = time.time()
        return cid

    def set_rgb_brightness(self, brightness: int, target_ip: str = "", cmd_id: str = "") -> dict:
        b = max(0, min(100, int(brightness)))
        self._rgb_brightness = b
        self.latest_feed["brightness"] = b
        cid = self._bump_feed_command("rgb", {"brightness": b}, cmd_id=cmd_id)
        if self.cloud_mode:
            return {"ok": True, "cloud_queued": True, "brightness": b, "cmd_id": cid}
        sent = self._post_esp_endpoint(f"/api/rgb?brightness={b}", body=None, target_ip=target_ip, timeout=1.8)
        return {"ok": True, "esp_reached": sent, "brightness": b, "ip": self.esp_wifi_ip, "cmd_id": cid}

    def send_page(self, target_ip: str = "", cmd_id: str = "") -> dict:
        cid = self._bump_feed_command("page", {}, cmd_id=cmd_id)
        if self.cloud_mode:
            return {"ok": True, "cloud_queued": True, "cmd_id": cid}
        sent = self._post_esp_endpoint("/api/page", body=None, target_ip=target_ip, timeout=1.8)
        return {"ok": True, "esp_reached": sent, "ip": self.esp_wifi_ip, "cmd_id": cid}

    def send_clear(self, target_ip: str = "", cmd_id: str = "") -> dict:
        self.latest_feed["state"] = "READY"
        self.latest_feed["question"] = ""
        self.latest_feed["text"] = ""
        cid = self._bump_feed_command("clear", {}, cmd_id=cmd_id)
        if self.cloud_mode:
            return {"ok": True, "cloud_queued": True, "cmd_id": cid}
        sent = self._post_esp_endpoint("/api/clear", body=None, target_ip=target_ip, timeout=1.8)
        self._last_sent_state = "READY"
        self._last_sent_time = time.time()
        return {"ok": True, "esp_reached": sent, "ip": self.esp_wifi_ip, "cmd_id": cid}

    def send_tft_image_rgb565(
        self,
        prompt: str,
        style: str,
        aspect: str,
        x: int,
        y: int,
        w: int,
        h: int,
        chunks: list,
        target_ip: str = "",
        cmd_id: str = ""
    ) -> dict:
        meta_payload = {
            "prompt": (prompt or "AI Art")[:120],
            "style": style or "Photorealistic",
            "aspect": aspect or "1:1",
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "chunks": chunks or []
        }
        cid = self._bump_feed_command("tft_image", meta_payload, cmd_id=cmd_id)
        if self.cloud_mode:
            return {"ok": True, "cloud_queued": True, "chunks": len(chunks or []), "cmd_id": cid}

        ok_start = self._post_esp_endpoint(
            "/api/tft/image/start",
            {"x": int(x), "y": int(y), "w": int(w), "h": int(h), "prompt": prompt[:80], "style": style, "aspect": aspect},
            target_ip=target_ip,
            timeout=2.5,
        )
        if not ok_start:
            return {"ok": False, "esp_reached": False, "detail": "ESP32 TFT unreachable", "cmd_id": cid}

        sent_chunks = 0
        for ch in (chunks or []):
            ok_c = self._post_esp_endpoint("/api/tft/image/chunk", ch, target_ip=target_ip, timeout=2.5)
            if ok_c:
                sent_chunks += 1
        self._post_esp_endpoint("/api/tft/image/finish", {"style": style, "aspect": aspect}, target_ip=target_ip, timeout=2.5)
        return {"ok": True, "esp_reached": True, "chunks_sent": sent_chunks, "ip": self.esp_wifi_ip, "cmd_id": cid}

    def execute_command(self, data: dict) -> dict:
        action = (data.get("action") or "feed").lower().strip()
        target_ip = (data.get("target_ip") or "").strip()
        cmd_id = (data.get("cmd_id") or "").strip()
        if cmd_id and cmd_id in self._seen_cmd_ids:
            return {"ok": True, "deduped": True, "cmd_id": cmd_id}

        if action == "rgb":
            return self.set_rgb_brightness(int(data.get("brightness", 45)), target_ip=target_ip, cmd_id=cmd_id)
        if action == "page":
            return self.send_page(target_ip=target_ip, cmd_id=cmd_id)
        if action == "clear":
            return self.send_clear(target_ip=target_ip, cmd_id=cmd_id)
        if action == "tft_image":
            return self.send_tft_image_rgb565(
                prompt=data.get("prompt", "AI Art"),
                style=data.get("style", "Photorealistic"),
                aspect=data.get("aspect", "1:1"),
                x=int(data.get("x", 90)),
                y=int(data.get("y", 62)),
                w=int(data.get("w", 140)),
                h=int(data.get("h", 140)),
                chunks=data.get("chunks") or [],
                target_ip=target_ip,
                cmd_id=cmd_id,
            )

        # Default: text feed update
        state = data.get("state") or "ANSWERED"
        question = data.get("question") or data.get("q") or data.get("prompt") or ""
        provider = data.get("provider") or "Gemini"
        model = data.get("model") or "GENESIS AI 5.0"
        text = data.get("text") or data.get("answer") or ""
        cid = cmd_id or f"feed_{int(time.time() * 1000)}"
        self._seen_cmd_ids.append(cid)
        ok = self.send_feed(state, question, provider, model, text, cmd_id=cid)
        return {"ok": ok, "action": "feed", "state": state, "cmd_id": cid, "bridge_info": self.get_status()}

    def start_cloud_poller(self, relay_url: str = "https://omni-model-ai-gateway.vercel.app"):
        if self.cloud_mode or self._cloud_poller_started:
            return
        self._cloud_poller_started = True
        base = relay_url.rstrip("/")

        def poll_loop():
            last_v = 0
            while True:
                try:
                    req = urllib.request.Request(f"{base}/api/screen/poll?v={last_v}", headers={"User-Agent": "GenesisLocalSync/1.0"})
                    with urllib.request.urlopen(req, timeout=4.0) as r:
                        if r.status == 200:
                            data = json.loads(r.read().decode("utf-8"))
                            if data.get("changed"):
                                last_v = data.get("version", last_v)
                                cid = data.get("cmd_id", "")
                                # Skip initial default template or already processed local commands
                                if cid and cid != "init" and cid not in self._seen_cmd_ids:
                                    action = data.get("action", "feed")
                                    payload = data.get("command_payload") or {}
                                    cmd_obj = {
                                        "action": action,
                                        "cmd_id": cid,
                                        "state": data.get("state", "ANSWERED"),
                                        "question": data.get("question", ""),
                                        "text": data.get("text", ""),
                                        "provider": data.get("provider", "Gemini"),
                                        "model": data.get("model", "GENESIS AI 5.0"),
                                        "brightness": data.get("brightness", payload.get("brightness", 45)),
                                        **payload,
                                    }
                                    self.execute_command(cmd_obj)
                except Exception:
                    pass
                time.sleep(2.0)

        threading.Thread(target=poll_loop, daemon=True).start()


# Global singleton instance
hardware_bridge = HardwareScreenBridge()
