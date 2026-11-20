import os
import sys
import time
import subprocess

GATEWAY_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    cmd = [sys.executable, "-u", "server.py"]
    while True:
        try:
            p = subprocess.Popen(cmd, cwd=GATEWAY_DIR)
            p.wait()
        except Exception:
            pass
        time.sleep(2)

if __name__ == "__main__":
    main()
