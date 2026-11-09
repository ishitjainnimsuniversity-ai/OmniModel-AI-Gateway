import importlib
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = {
            "python": sys.version,
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "root_dir": str(ROOT_DIR),
            "root_entries": sorted(os.listdir(ROOT_DIR)) if ROOT_DIR.exists() else [],
            "sys_path": sys.path[:8],
            "vercel_env_flags": {
                k: bool(os.getenv(k))
                for k in (
                    "VERCEL",
                    "VERCEL_ENV",
                    "VERCEL_URL",
                    "AWS_LAMBDA_FUNCTION_NAME",
                    "AWS_EXECUTION_ENV",
                    "LAMBDA_TASK_ROOT",
                )
            },
            "imports": {},
        }
        for mod in (
            "fastapi",
            "starlette",
            "pydantic",
            "uvicorn",
            "httpx",
            "dotenv",
            "aiofiles",
            "core.config",
            "server",
        ):
            try:
                m = importlib.import_module(mod)
                info = {"ok": True, "version": getattr(m, "__version__", None)}
                if mod == "server":
                    info["core_error"] = getattr(m, "_CORE_IMPORT_ERROR", None)
                    info["has_app"] = hasattr(m, "app")
                results["imports"][mod] = info
            except Exception as exc:
                results["imports"][mod] = {
                    "ok": False,
                    "error": repr(exc),
                    "traceback": traceback.format_exc().splitlines()[-15:],
                }

        body = json.dumps(results, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
