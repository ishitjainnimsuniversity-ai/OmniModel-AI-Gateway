"""
OmniModel AI Universal Gateway Server
Vercel Zero-Config FastAPI & local uvicorn entrypoint (`server:app`).
"""

import sys
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

app = FastAPI(
    title="OmniModel Universal AI Gateway",
    description="2026 Master Multi-Model Hub & Router for Antigravity",
    version="2.0.0",
)

_BOOT_ERROR: Optional[str] = None
_CORE_IMPORT_ERROR: Optional[str] = None
_gateway_main = None

try:
    import gateway_runtime as _gr

    _CORE_IMPORT_ERROR = getattr(_gr, "_CORE_IMPORT_ERROR", None)
    _gateway_main = _gr.main
    app = _gr.app
except Exception:
    _BOOT_ERROR = traceback.format_exc()
    print(f"[server.py] Boot error:\n{_BOOT_ERROR}", file=sys.stderr)

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def _boot_diag(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "boot_error",
                "path": full_path,
                "error": _BOOT_ERROR,
            },
        )


def main():
    if _gateway_main is not None:
        _gateway_main()
    elif _BOOT_ERROR:
        raise RuntimeError(_BOOT_ERROR)


if __name__ == "__main__":
    main()
