"""
OmniModel AI Universal Gateway Server Launcher
Starts gateway_runtime:app locally cleanly while keeping Vercel serverless functions isolated in api/.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main():
    from gateway_runtime import main as run_gateway

    run_gateway()


if __name__ == "__main__":
    main()
