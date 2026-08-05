"""Phase 2 autopilot — find French consumers (no WA verify, no Firecrawl)."""

from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import SystemMetric
from app.services.pipeline import utcnow

logger = logging.getLogger(__name__)

KEY = "demand_autopilot"
_lock = threading.Lock()
_thread: threading.Thread | None = None
_stop = threading.Event()
_state: dict[str, Any] = {
    "enabled": True,
    "running": False,
    "cycle": 0,
    "last_result": None,
    "last_error": None,
    "phase": "idle",
}


def _get_row(db) -> SystemMetric:
    row = db.scalar(select(SystemMetric).where(SystemMetric.key == KEY))
    if not row:
        row = SystemMetric(
            key=KEY,
            value={
                "enabled": True,
                "sleep_sec": 120,
                "supplier_limit": 25,
                "query_limit": 15,
                "enrich_limit": 20,
                "include_platforms": True,
            },
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_config() -> dict[str, Any]:
    db = SessionLocal()
    try:
        row = _get_row(db)
        val = dict(row.value or {})
        val.setdefault("enabled", True)
        val.setdefault("sleep_sec", 120)
        val.setdefault("supplier_limit", 25)
        val.setdefault("query_limit", 15)
        val.setdefault("enrich_limit", 20)
        val.setdefault("include_platforms", True)
        return val
    finally:
        db.close()


def status_snapshot() -> dict[str, Any]:
    cfg = get_config()
    with _lock:
        live = dict(_state)
    return {**live, **cfg, "thread_alive": bool(_thread and _thread.is_alive())}


def _loop() -> None:
    from app.services.demand_discovery import demand_stats, run_demand_cycle

    logger.info("Demand autopilot started (Phase 2 — consumer find)")
    while not _stop.is_set():
        cfg = get_config()
        if not cfg.get("enabled", True):
            with _lock:
                _state["phase"] = "paused"
                _state["running"] = False
            _stop.wait(10)
            continue

        cycle_n = 0
        with _lock:
            _state["running"] = True
            cycle_n = int(_state.get("cycle") or 0) + 1
            _state["cycle"] = cycle_n
            if cycle_n % 3 == 0:
                _state["phase"] = "platforms"
            elif cycle_n % 3 == 1:
                _state["phase"] = "reverse_fr"
            else:
                _state["phase"] = "enrich"

        db = SessionLocal()
        try:
            include_platforms = bool(cfg.get("include_platforms", True))
            result = run_demand_cycle(
                db,
                supplier_limit=int(cfg.get("supplier_limit", 25)),
                query_limit=int(cfg.get("query_limit", 15)),
                enrich_limit=int(cfg.get("enrich_limit", 20)),
                include_platforms=include_platforms,
                include_enrich=True,
            )
            result["stats"] = demand_stats(db)
            with _lock:
                _state["last_result"] = result
                _state["last_error"] = None
                _state["phase"] = "sleep"
            logger.info(
                "Demand cycle +%s consumers (total=%s, FR=%s)",
                result.get("consumers_gained"),
                result.get("consumers_after"),
                result.get("fr_leads"),
            )
        except Exception as exc:
            logger.exception("Demand cycle failed")
            with _lock:
                _state["last_error"] = str(exc)[:400]
                _state["phase"] = "error"
        finally:
            with _lock:
                _state["running"] = False
            db.close()

        sleep_sec = max(30, int(cfg.get("sleep_sec", 120)))
        _stop.wait(sleep_sec)

    logger.info("Demand autopilot stopped")


def start_demand_autopilot_thread() -> None:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="wareach-demand-autopilot", daemon=True)
        _thread.start()
        logger.info("Demand autopilot ON")


def stop_demand_autopilot_thread() -> None:
    _stop.set()
