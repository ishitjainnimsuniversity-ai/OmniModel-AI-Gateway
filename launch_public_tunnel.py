"""
ALFA AI 5.0 Live Public Tunnel Launcher
Connects local port 8000 to a public HTTPS domain via SSH reverse tunnel.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_URL_FILE = BASE_DIR / "LIVE_PUBLIC_URL.txt"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log("Starting ALFA AI 5.0 Public Tunnel...")

while True:
    try:
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "-R", "80:localhost:8000", "nokey@localhost.run"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            line_clean = line.strip()
            log(f"Tunnel: {line_clean}")

            # Extract https url
            match = re.search(r"https://[a-zA-Z0-9\-\.]+\.lhr\.(?:life|pro|run)", line_clean)
            if match:
                url = match.group(0)
                log(f"\n=======================================================")
                log(f"[LIVE PUBLIC URL] ALFA AI 5.0 is live at: {url}")
                log(f"=======================================================\n")
                PUBLIC_URL_FILE.write_text(f"ALFA AI 5.0 Live Public URL:\n{url}\n\nLocal: http://127.0.0.1:8000\n", encoding="utf-8")

        process.wait()
    except Exception as e:
        log(f"Tunnel error: {e}")
    time.sleep(5)
