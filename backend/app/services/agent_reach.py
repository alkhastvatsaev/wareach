"""Agent Reach integration — health + upstream tool routing."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ChannelStatus:
    name: str
    status: str
    active_backend: str | None
    message: str


def _which(bin_name: str) -> str | None:
    return shutil.which(bin_name)


def run_doctor() -> dict[str, Any]:
    """Run `agent-reach doctor --json` and return parsed channels."""
    bin_path = _which(settings.agent_reach_bin) or settings.agent_reach_bin
    try:
        proc = subprocess.run(
            [bin_path, "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        raw = proc.stdout.strip() or proc.stderr.strip()
        # doctor may print non-json noise — find JSON object
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(raw[start : end + 1])
        else:
            data = {"_parse_error": True, "raw": raw[:2000], "returncode": proc.returncode}
        return data
    except FileNotFoundError:
        return {"_error": "agent-reach not found", "hint": "Install from https://github.com/Panniantong/agent-reach"}
    except Exception as exc:
        logger.exception("doctor failed")
        return {"_error": str(exc)}


def summarize_doctor(data: dict[str, Any]) -> list[ChannelStatus]:
    out: list[ChannelStatus] = []
    for key, val in data.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        out.append(
            ChannelStatus(
                name=key,
                status=str(val.get("status", "unknown")),
                active_backend=val.get("active_backend"),
                message=str(val.get("message", ""))[:500],
            )
        )
    return out


def discovery_backends_ready(doctor: dict[str, Any] | None = None) -> dict[str, bool]:
    doctor = doctor or run_doctor()
    exa = doctor.get("exa_search", {})
    web = doctor.get("web", {})
    web_status = str(web.get("status") or "ok").lower()
    return {
        "agent_reach": "_error" not in doctor,
        "exa": exa.get("status") in {"ok", "warn"} or _which(settings.mcporter_bin) is not None,
        # Jina Reader is plain HTTP; only false if doctor explicitly failed it
        "jina_web": web_status not in {"error", "fail", "down"},
        "mcporter": _which(settings.mcporter_bin) is not None,
    }
