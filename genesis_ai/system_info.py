"""Windows system resource inspection and Ollama model recommender for GENESIS AI."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional
import httpx
import psutil

from .settings import settings


class SystemInspector:
    @staticmethod
    def get_hardware_specs() -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        cores_phys = psutil.cpu_count(logical=False) or 4
        cores_log = psutil.cpu_count(logical=True) or 8

        gpu_name = "Integrated / Software"
        vram_mb = 0
        if os.name == "nt":
            try:
                # Query WMIC or PowerShell for VideoController
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-CimInstance Win32_VideoController | Select-Object -First 1 -ExpandProperty Name"],
                    timeout=3, text=True
                ).strip()
                if out:
                    gpu_name = out
            except Exception:
                pass

        return {
            "ram_total_gb": round(vm.total / (1024**3), 2),
            "ram_avail_gb": round(vm.available / (1024**3), 2),
            "ram_used_percent": vm.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "cpu_cores_physical": cores_phys,
            "cpu_cores_logical": cores_log,
            "gpu_name": gpu_name,
        }

    @staticmethod
    async def get_ollama_models() -> List[Dict[str, Any]]:
        url = f"{settings.ollama_base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    models = []
                    for m in data.get("models", []):
                        size_gb = round(m.get("size", 0) / (1024**3), 2)
                        models.append({
                            "name": m.get("name", ""),
                            "size_gb": size_gb,
                            "modified_at": m.get("modified_at", ""),
                            "family": m.get("details", {}).get("family", ""),
                            "parameter_size": m.get("details", {}).get("parameter_size", ""),
                            "quantization": m.get("details", {}).get("quantization_level", "")
                        })
                    return models
        except Exception:
            pass
        return []

    @classmethod
    async def get_recommendations(cls) -> Dict[str, Any]:
        specs = cls.get_hardware_specs()
        installed_models = await cls.get_ollama_models()
        avail_ram = specs["ram_avail_gb"]
        free_disk = specs["disk_free_gb"]

        # Resource-aware tier evaluation
        if avail_ram < 2.5:
            rec_model = "llama3.2:1b"
            reason = (f"Available RAM is {avail_ram:.1f} GB. llama3.2:1b uses ~1.3 GB and runs entirely in memory "
                      f"without swapping, providing 25-35 tokens/sec CPU inference on {specs['cpu_cores_physical']}-core Ryzen.")
        elif avail_ram < 5.5:
            rec_model = "llama3.2:3b"
            reason = (f"Available RAM is {avail_ram:.1f} GB. llama3.2:3b uses ~2.2 GB and offers enhanced reasoning "
                      f"while remaining within safe memory bounds.")
        else:
            rec_model = "qwen2.5:7b"
            reason = (f"Available RAM is {avail_ram:.1f} GB. 7B models offer top-tier offline intelligence.")

        active_local = settings.local_model
        is_installed = any(m["name"] == active_local or m["name"].startswith(f"{active_local}:") for m in installed_models)

        return {
            "specs": specs,
            "installed_models": installed_models,
            "recommended_model": rec_model,
            "recommendation_reason": reason,
            "active_local_model": active_local,
            "active_model_installed": is_installed,
            "ollama_running": len(installed_models) > 0,
            "safe_to_download_3b": free_disk > 5.0 and avail_ram >= 2.5,
            "safe_to_download_7b": free_disk > 10.0 and avail_ram >= 6.0
        }
