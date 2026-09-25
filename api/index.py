import sys
import os
import traceback
from pathlib import Path

# Add project root and api dir to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = Path(__file__).resolve().parent

for p in (str(ROOT_DIR), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from server import app
except Exception as e:
    import json
    from http.server import BaseHTTPRequestHandler

    tb = traceback.format_exc()
    print(f"Server import failed: {e}\n{tb}", file=sys.stderr)

    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        app = FastAPI()

        @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
        async def catch_all_debug(path: str = ""):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "server_import_failed",
                    "details": str(e),
                    "traceback": tb.splitlines()
                }
            )
    except Exception as fastapi_err:
        class handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "fastapi_not_available",
                    "import_error": str(e),
                    "fastapi_error": str(fastapi_err),
                    "traceback": tb.splitlines()
                }).encode('utf-8'))

            def do_POST(self):
                self.do_GET()

