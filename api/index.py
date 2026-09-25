import sys
import traceback
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from server import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    tb = traceback.format_exc()
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def catch_all_debug(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_import_failed",
                "details": str(e),
                "traceback": tb.splitlines()
            }
        )
