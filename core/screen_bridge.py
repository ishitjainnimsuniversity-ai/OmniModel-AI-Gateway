"""
Universal Screen Bridge for ESP32-C5 2.4-inch ILI9341 Screen
Supports DUAL HYBRID OPERATION:
1. Wi-Fi Network Synchronization (HTTP REST) - works anywhere in the room, on wall charger or battery.
2. USB Serial Synchronization (CDC COM4) - works with ultra-low latency when plugged into the laptop.
"""

import json
import os
import re
import socket
import threading
import time
import urllib.request

try:
    import serial
except ImportError:
    serial = None

IS_CLOUD_RUNTIME = bool(
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("RENDER")
    or os.getenv("DYNO")
    or os.getenv("RAILWAY_ENVIRONMENT")
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

        # Global Feed Cache for Worldwide Polling
        self.latest_feed = {
            "version": 1,
            "state": "READY",
            "question": "",
            "text": "",
            "provider": "Gemini",
            "model": "GENESIS AI 5.0",
            "timestamp": time.time()
        }

        # Wi-Fi Sync State
        self.esp_wifi_ip = "" if self.cloud_mode else default_ip
        self._wifi_ok = False
        self._last_scan_time = 0.0

        # Skip USB serial & LAN scanner background threads inside serverless/cloud containers
        if not self.cloud_mode:
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

    def get_status(self) -> dict:
        return {
            "cloud_mode": self.cloud_mode,
            "usb_connected": bool(self.ser and self.ser.is_open),
            "wifi_ip": self.esp_wifi_ip,
            "wifi_connected": self._wifi_ok,
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

    def send_feed(self, state: str, question: str, provider: str, model: str, text: str = ""):
        now = time.time()
        # Debounce duplicate identical states within 0.8 seconds
        if state == "ANSWERED" and self._last_sent_state == "ANSWERED" and (now - self._last_sent_time) < 0.8:
            return True

        clean_ans = self._sanitize_text(text)
        self.latest_feed["version"] = self.latest_feed.get("version", 0) + 1
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


# Global singleton instance
hardware_bridge = HardwareScreenBridge()
