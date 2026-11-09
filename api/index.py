import os
import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = Path(__file__).resolve().parent

for p in (str(ROOT_DIR), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from server import app
except Exception as e:
    tb = traceback.format_exc()
    print(f"[api/index.py] Failed to import server:app -> {e}\n{tb}", file=sys.stderr)
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="OmniModel Gateway Diagnostic Fallback")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def diagnostic_catch_all(path: str = ""):
        root_entries = []
        try:
            root_entries = sorted(os.listdir(ROOT_DIR))
        except Exception:
            pass
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_import_failed",
                "details": str(e),
                "traceback": tb.splitlines(),
                "root_dir": str(ROOT_DIR),
                "root_entries": root_entries,
            },
        )
