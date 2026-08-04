"""In-process autopilot — harvest + verify without Celery/Redis."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.migrate import reclaim_stale_url_jobs
from app.db.session import SessionLocal
from app.models.entities import SystemMetric
from app.services.pipeline import utcnow
from app.services.whatsapp_harvest import whatsapp_count

logger = logging.getLogger(__name__)

KEY = "autopilot"
_lock = threading.Lock()
_thread: threading.Thread | None = None
_stop = threading.Event()
_state: dict[str, Any] = {
    "enabled": True,
    "running": False,
    "cycle": 0,
    "last_started_at": None,
    "last_finished_at": None,
    "last_result": None,
    "last_error": None,
    "phase": "idle",
}


def _get_row(db: Session) -> SystemMetric:
    row = db.scalar(select(SystemMetric).where(SystemMetric.key == KEY))
    if not row:
        row = SystemMetric(
            key=KEY,
            value={
                "enabled": True,
                "verify_wa": True,
                "sleep_sec": 55,
                "wa_verify_every_n": 2,
            },
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_config(db: Session | None = None) -> dict[str, Any]:
    own = db is None
    if own:
        db = SessionLocal()
    try:
        row = _get_row(db)
        val = dict(row.value or {})
        val.setdefault("enabled", True)
        val.setdefault("verify_wa", True)
        val.setdefault("sleep_sec", 55)
        val.setdefault("wa_verify_every_n", 2)
        return val
    finally:
        if own:
            db.close()


def set_enabled(enabled: bool, *, verify_wa: bool | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        row = _get_row(db)
        val = dict(row.value or {})
        val["enabled"] = bool(enabled)
        if verify_wa is not None:
            val["verify_wa"] = bool(verify_wa)
        val["updated_at"] = utcnow().isoformat()
        row.value = val
        row.updated_at = utcnow()
        db.commit()
        with _lock:
            _state["enabled"] = bool(enabled)
        return status_snapshot()
    finally:
        db.close()


def status_snapshot() -> dict[str, Any]:
    cfg = get_config()
    with _lock:
        live = dict(_state)
    return {
        **live,
        "enabled": bool(cfg.get("enabled", True)),
        "verify_wa": bool(cfg.get("verify_wa", True)),
        "sleep_sec": int(cfg.get("sleep_sec", 55)),
        "wa_verify_every_n": int(cfg.get("wa_verify_every_n", 2)),
        "thread_alive": bool(_thread and _thread.is_alive()),
        "whatsapp": None,
    }


def run_cycle(db: Session, *, do_verify: bool = False) -> dict[str, Any]:
    """One full harvest cycle (SQLite-safe sequential)."""
    from app.services.alerts import evaluate_alerts
    from app.services.drain import drain_wa_pending
    from app.services.offline_harvest import offline_harvest_all
    from app.services.pipeline import run_crawl_batch
    from app.services.quality import dedup_whatsapp_variants
    from app.services.reharvest import reharvest_pending_snippets
    from app.services.wa_verify import auth_ready, run_whatsapp_verify
    from app.services.whatsapp_harvest import run_whatsapp_blitz
    from app.services.yupoo_expand import run_yupoo_expand
    from app.services.yupoo_raw import run_yupoo_raw_crawl

    before = whatsapp_count(db)
    reclaim_stale_url_jobs()
    result: dict[str, Any] = {
        "whatsapp_before": before,
        "offline": offline_harvest_all(db, limit=4000),
        "expand": run_yupoo_expand(db, seed_limit=20, prefer_contact=True),
        "raw": run_yupoo_raw_crawl(db, limit=35, workers=4),
        "drain": drain_wa_pending(db, limit=50, fetch_pages=False),
        "blitz": run_whatsapp_blitz(db, query_limit=14, workers=3),
        "crawl": run_crawl_batch(db, limit=18),
        "reharvest": reharvest_pending_snippets(db, limit=500),
        "dedup": dedup_whatsapp_variants(db),
    }
    if do_verify and auth_ready():
        try:
            result["wa_verify"] = run_whatsapp_verify(db, limit=20, delay_ms=3500)
        except Exception as exc:
            result["wa_verify"] = {"ok": False, "error": str(exc)[:300]}
    elif do_verify:
        result["wa_verify"] = {"ok": False, "skipped": "no_session"}
    try:
        result["alerts"] = evaluate_alerts(db)
    except Exception as exc:
        result["alerts"] = {"error": str(exc)[:200]}
    after = whatsapp_count(db)
    result["whatsapp_after"] = after
    result["whatsapp_gained"] = max(0, after - before)
    return result


def _loop() -> None:
    logger.info("Autopilot thread started")
    while not _stop.is_set():
        cfg = get_config()
        enabled = bool(cfg.get("enabled", True))
        with _lock:
            _state["enabled"] = enabled
        if not enabled:
            with _lock:
                _state["phase"] = "paused"
                _state["running"] = False
            _stop.wait(5)
            continue

        with _lock:
            _state["running"] = True
            _state["phase"] = "harvest"
            _state["last_started_at"] = utcnow().isoformat()
            _state["cycle"] = int(_state.get("cycle") or 0) + 1
            cycle = int(_state["cycle"])

        every = max(1, int(cfg.get("wa_verify_every_n", 2)))
        do_verify = bool(cfg.get("verify_wa", True)) and (cycle % every == 0)
        db = SessionLocal()
        try:
            result = run_cycle(db, do_verify=do_verify)
            with _lock:
                _state["last_result"] = {
                    "whatsapp_gained": result.get("whatsapp_gained"),
                    "whatsapp_after": result.get("whatsapp_after"),
                    "wa_verify": (result.get("wa_verify") or {}).get("ok"),
                }
                _state["last_error"] = None
                _state["last_finished_at"] = utcnow().isoformat()
                _state["phase"] = "sleep"
            logger.info(
                "Autopilot cycle %s done — +%s WA (total=%s)",
                cycle,
                result.get("whatsapp_gained"),
                result.get("whatsapp_after"),
            )
        except Exception as exc:
            logger.exception("Autopilot cycle failed")
            with _lock:
                _state["last_error"] = str(exc)[:400]
                _state["phase"] = "error"
                _state["last_finished_at"] = utcnow().isoformat()
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            with _lock:
                _state["running"] = False
            db.close()

        sleep_sec = max(20, int(cfg.get("sleep_sec", 55)))
        _stop.wait(sleep_sec)

    logger.info("Autopilot thread stopped")


def start_autopilot_thread() -> None:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return
        _stop.clear()
        # Default ON
        try:
            cfg = get_config()
            _state["enabled"] = bool(cfg.get("enabled", True))
        except Exception:
            _state["enabled"] = True
        _thread = threading.Thread(target=_loop, name="wareach-autopilot", daemon=True)
        _thread.start()
        logger.info("Autopilot enabled=%s", _state["enabled"])


def stop_autopilot_thread() -> None:
    _stop.set()
