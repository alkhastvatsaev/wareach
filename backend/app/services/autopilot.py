"""In-process autopilot — harvest + WA verify in parallel (no Celery required)."""

from __future__ import annotations

import logging
import threading
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
_harvest_thread: threading.Thread | None = None
_verify_thread: threading.Thread | None = None
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
    "verify_running": False,
    "verify_phase": "idle",
    "verify_cycle": 0,
    "last_verify_result": None,
    "last_verify_error": None,
    "last_verify_at": None,
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
                "wa_verify_every_n": 1,
                "wa_verify_limit": 25,
                "wa_verify_delay_ms": 3500,
                "wa_verify_sleep_sec": 20,
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
        val.setdefault("wa_verify_every_n", 1)
        val.setdefault("wa_verify_limit", 25)
        val.setdefault("wa_verify_delay_ms", 3500)
        val.setdefault("wa_verify_sleep_sec", 20)
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
        "wa_verify_every_n": int(cfg.get("wa_verify_every_n", 1)),
        "wa_verify_limit": int(cfg.get("wa_verify_limit", 25)),
        "wa_verify_sleep_sec": int(cfg.get("wa_verify_sleep_sec", 20)),
        "thread_alive": bool(_harvest_thread and _harvest_thread.is_alive()),
        "verify_thread_alive": bool(_verify_thread and _verify_thread.is_alive()),
        "parallel": True,
        "whatsapp": None,
    }


def run_cycle(db: Session, *, do_verify: bool = False) -> dict[str, Any]:
    """Harvest cycle only. WA verify runs on its own parallel thread."""
    from app.services.alerts import evaluate_alerts
    from app.services.drain import drain_wa_pending
    from app.services.offline_harvest import offline_harvest_all
    from app.services.pipeline import run_crawl_batch
    from app.services.quality import dedup_whatsapp_variants
    from app.services.reharvest import reharvest_pending_snippets
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
    # Optional inline verify kept for /autopilot/tick?verify=true
    if do_verify:
        from app.services.wa_verify import auth_ready, run_whatsapp_verify

        if auth_ready():
            try:
                result["wa_verify"] = run_whatsapp_verify(db, limit=20, delay_ms=3500)
            except Exception as exc:
                result["wa_verify"] = {"ok": False, "error": str(exc)[:300]}
        else:
            result["wa_verify"] = {"ok": False, "skipped": "no_session"}
    try:
        result["alerts"] = evaluate_alerts(db)
    except Exception as exc:
        result["alerts"] = {"error": str(exc)[:200]}
    after = whatsapp_count(db)
    result["whatsapp_after"] = after
    result["whatsapp_gained"] = max(0, after - before)
    return result


def _harvest_loop() -> None:
    logger.info("Autopilot harvest thread started")
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

        db = SessionLocal()
        try:
            result = run_cycle(db, do_verify=False)
            with _lock:
                prev = dict(_state.get("last_result") or {})
                _state["last_result"] = {
                    **prev,
                    "whatsapp_gained": result.get("whatsapp_gained"),
                    "whatsapp_after": result.get("whatsapp_after"),
                }
                _state["last_error"] = None
                _state["last_finished_at"] = utcnow().isoformat()
                _state["phase"] = "sleep"
            logger.info(
                "Harvest cycle %s done — +%s WA (total=%s)",
                cycle,
                result.get("whatsapp_gained"),
                result.get("whatsapp_after"),
            )
        except Exception as exc:
            logger.exception("Harvest cycle failed")
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

    logger.info("Autopilot harvest thread stopped")


def _verify_loop() -> None:
    """Continuous Baileys verify — runs in parallel with harvest."""
    from app.services.wa_verify import auth_ready, run_whatsapp_verify

    logger.info("Autopilot WA-verify thread started")
    while not _stop.is_set():
        cfg = get_config()
        enabled = bool(cfg.get("enabled", True))
        verify_on = bool(cfg.get("verify_wa", True))
        if not enabled or not verify_on:
            with _lock:
                _state["verify_running"] = False
                _state["verify_phase"] = "paused" if enabled else "off"
            _stop.wait(5)
            continue

        if not auth_ready():
            with _lock:
                _state["verify_running"] = False
                _state["verify_phase"] = "no_session"
                _state["last_verify_error"] = "WhatsApp session manquante"
            _stop.wait(30)
            continue

        limit = max(5, int(cfg.get("wa_verify_limit", 25)))
        delay_ms = max(1500, int(cfg.get("wa_verify_delay_ms", 3500)))
        with _lock:
            _state["verify_running"] = True
            _state["verify_phase"] = "verifying"
            _state["verify_cycle"] = int(_state.get("verify_cycle") or 0) + 1
            vcycle = int(_state["verify_cycle"])

        db = SessionLocal()
        try:
            result = run_whatsapp_verify(db, limit=limit, delay_ms=delay_ms)
            with _lock:
                _state["last_verify_result"] = {
                    "ok": result.get("ok"),
                    "checked": (result.get("import") or {}).get("imported")
                    or result.get("checked")
                    or result.get("pending_count"),
                    "reachable": (result.get("import") or {}).get("reachable"),
                    "dead": (result.get("import") or {}).get("dead"),
                }
                prev = dict(_state.get("last_result") or {})
                prev["wa_verify"] = bool(result.get("ok"))
                _state["last_result"] = prev
                _state["last_verify_error"] = None if result.get("ok") else str(result.get("error") or "")[:300]
                _state["last_verify_at"] = utcnow().isoformat()
                _state["verify_phase"] = "sleep"
            logger.info("WA verify cycle %s — %s", vcycle, _state["last_verify_result"])
        except Exception as exc:
            logger.exception("WA verify cycle failed")
            with _lock:
                _state["last_verify_error"] = str(exc)[:400]
                _state["verify_phase"] = "error"
                _state["last_verify_at"] = utcnow().isoformat()
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            with _lock:
                _state["verify_running"] = False
            db.close()

        sleep_sec = max(10, int(cfg.get("wa_verify_sleep_sec", 20)))
        _stop.wait(sleep_sec)

    logger.info("Autopilot WA-verify thread stopped")


def start_autopilot_thread() -> None:
    global _harvest_thread, _verify_thread
    with _lock:
        if _harvest_thread and _harvest_thread.is_alive() and _verify_thread and _verify_thread.is_alive():
            return
        _stop.clear()
        try:
            cfg = get_config()
            _state["enabled"] = bool(cfg.get("enabled", True))
        except Exception:
            _state["enabled"] = True
        if not (_harvest_thread and _harvest_thread.is_alive()):
            _harvest_thread = threading.Thread(
                target=_harvest_loop, name="wareach-autopilot-harvest", daemon=True
            )
            _harvest_thread.start()
        if not (_verify_thread and _verify_thread.is_alive()):
            _verify_thread = threading.Thread(
                target=_verify_loop, name="wareach-autopilot-verify", daemon=True
            )
            _verify_thread.start()
        logger.info(
            "Autopilot parallel ON (harvest+verify) enabled=%s",
            _state["enabled"],
        )


def stop_autopilot_thread() -> None:
    _stop.set()
