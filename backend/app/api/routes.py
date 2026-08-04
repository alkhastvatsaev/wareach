from __future__ import annotations

import csv
import io
from typing import Any

import redis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import Contact, DiscoveredUrl, JobRun, SearchQuery, Supplier, SystemMetric
from app.schemas.api import ContactOut, HealthOut, JobTriggerOut, StatsOut, SupplierOut
from app.services.agent_reach import discovery_backends_ready, run_doctor, summarize_doctor
from app.services.pipeline import run_crawl_batch, run_discovery_batch, stats_overview

router = APIRouter()
settings = get_settings()


@router.get("/ping")
def ping():
    """Ultra-light liveness — never runs doctor / heavy IO."""
    return {"ok": True, "app": settings.app_name}


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    # Prefer cached doctor only — never block health on run_doctor() (can take 60s)
    doctor: dict[str, Any] = {}
    from_cache = False
    try:
        row = db.scalar(select(SystemMetric).where(SystemMetric.key == "agent_reach_doctor"))
        if row and isinstance(row.value, dict) and row.value:
            doctor = row.value
            from_cache = True
    except Exception:
        doctor = {}

    db_ok = True
    try:
        db.execute(select(1))
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=0.8)
        redis_ok = r.ping() is True
    except Exception:
        redis_ok = False

    backends = discovery_backends_ready(doctor) if doctor else {"exa": False, "jina_web": False}
    # DB up ⇒ ok (engines may warm in background)
    status = "ok" if db_ok else "down"
    if db_ok and doctor and not (backends.get("exa") or backends.get("jina_web")):
        status = "degraded"
    return HealthOut(
        status=status,
        agent_reach={
            "channels": [c.__dict__ for c in summarize_doctor(doctor)] if doctor else [],
            "raw_keys": [k for k in doctor.keys() if not k.startswith("_")],
            "error": doctor.get("_error"),
            "cached": from_cache,
        },
        backends=backends,
        database=db_ok,
        redis=redis_ok,
    )


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    return StatsOut(**stats_overview(db), target_suppliers=10000)


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_db),
    brand: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    lead_type: str | None = None,
    quality_tier: str | None = None,
    group: str | None = None,
    min_score: float = 0,
    q: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
):
    stmt = select(Supplier).order_by(
        Supplier.priority_score.desc(),
        Supplier.risk_score.desc(),
        Supplier.last_seen_at.desc(),
    )
    if status:
        stmt = stmt.where(Supplier.status == status)
    if platform:
        stmt = stmt.where(Supplier.primary_platform == platform)
    if lead_type:
        stmt = stmt.where(Supplier.lead_type == lead_type)
    if quality_tier:
        stmt = stmt.where(Supplier.quality_tier == quality_tier)
    if min_score:
        stmt = stmt.where(Supplier.risk_score >= min_score)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Supplier.display_name.ilike(like))
            | (Supplier.canonical_key.ilike(like))
            | (Supplier.primary_url.ilike(like))
        )
    fetch_n = max(limit + offset, 400) if (brand or group) else offset + limit
    rows = list(db.scalars(stmt.offset(0).limit(fetch_n)).all())
    if brand:
        rows = [r for r in rows if brand in (r.brands or [])]
    if group:
        rows = [r for r in rows if group in (getattr(r, "groups", None) or [])]
    return rows[offset : offset + limit]


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    row = db.get(Supplier, supplier_id)
    if not row:
        raise HTTPException(404, "Supplier not found")
    return row


@router.get("/suppliers/{supplier_id}/contacts", response_model=list[ContactOut])
def supplier_contacts(supplier_id: int, db: Session = Depends(get_db)):
    rows = list(
        db.scalars(select(Contact).where(Contact.supplier_id == supplier_id).order_by(Contact.contact_type)).all()
    )
    return [_serialize_contact(c) for c in rows]


@router.patch("/suppliers/{supplier_id}/status")
def update_status(supplier_id: int, status: str, db: Session = Depends(get_db)):
    allowed = {"new", "reviewing", "confirmed", "escalated", "closed"}
    if status not in allowed:
        raise HTTPException(400, f"status must be one of {allowed}")
    row = db.get(Supplier, supplier_id)
    if not row:
        raise HTTPException(404, "Supplier not found")
    row.status = status
    db.commit()
    return {"ok": True, "id": supplier_id, "status": status}


def _contact_open_url(c: Contact) -> str | None:
    if c.contact_type == "whatsapp":
        digits = "".join(ch for ch in c.normalized_value if ch.isdigit())
        if digits:
            return f"https://wa.me/{digits}"
    if c.contact_type == "wechat":
        # WeChat has no public deep-link; return search hint page
        return f"weixin://contacts/profile/{c.normalized_value}"
    if c.contact_type == "telegram":
        handle = c.normalized_value.lstrip("@")
        return f"https://t.me/{handle}"
    return None


def _serialize_contact(c: Contact) -> ContactOut:
    return ContactOut(
        id=c.id,
        supplier_id=c.supplier_id,
        contact_type=c.contact_type,
        raw_value=c.raw_value,
        normalized_value=c.normalized_value,
        source_url=c.source_url,
        brand_context=c.brand_context,
        seen_count=c.seen_count or 1,
        verify_status=getattr(c, "verify_status", None) or "unverified",
        verify_note=getattr(c, "verify_note", None),
        verified_at=getattr(c, "verified_at", None),
        first_seen_at=c.first_seen_at,
        last_seen_at=c.last_seen_at,
        open_url=_contact_open_url(c),
    )


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(
    db: Session = Depends(get_db),
    contact_type: str | None = None,
    verify_status: str | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
):
    stmt = select(Contact).order_by(Contact.last_seen_at.desc())
    if contact_type:
        if contact_type == "messageable":
            stmt = stmt.where(Contact.contact_type.in_(["whatsapp", "wechat", "telegram"]))
        else:
            stmt = stmt.where(Contact.contact_type == contact_type)
    if verify_status:
        if verify_status == "unverified":
            stmt = stmt.where(
                or_(Contact.verify_status == "unverified", Contact.verify_status.is_(None))
            )
        else:
            stmt = stmt.where(Contact.verify_status == verify_status)
    rows = list(db.scalars(stmt.offset(offset).limit(limit)).all())
    return [_serialize_contact(c) for c in rows]


@router.patch("/contacts/{contact_id}/verify")
def verify_contact(
    contact_id: int,
    status: str,
    note: str | None = None,
    db: Session = Depends(get_db),
):
    allowed = {"unverified", "reachable", "dead", "busy", "skip"}
    if status not in allowed:
        raise HTTPException(400, f"status must be one of {allowed}")
    row = db.get(Contact, contact_id)
    if not row:
        raise HTTPException(404, "Contact not found")
    from app.services.pipeline import utcnow

    row.verify_status = status
    row.verify_note = (note or "")[:255] or None
    row.verified_at = utcnow()
    db.commit()
    return {"ok": True, "id": contact_id, "verify_status": status, "open_url": _contact_open_url(row)}


@router.get("/urls")
def list_urls(
    db: Session = Depends(get_db),
    status: str | None = "pending",
    limit: int = Query(50, le=500),
):
    stmt = select(DiscoveredUrl).order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.id.desc())
    if status:
        stmt = stmt.where(DiscoveredUrl.status == status)
    rows = db.scalars(stmt.limit(limit)).all()
    return [
        {
            "id": r.id,
            "url": r.url,
            "domain": r.domain,
            "status": r.status,
            "brand_hint": r.brand_hint,
            "priority": r.priority,
            "title": r.title,
        }
        for r in rows
    ]


@router.get("/queries")
def list_queries(db: Session = Depends(get_db), limit: int = 200):
    rows = db.scalars(select(SearchQuery).order_by(SearchQuery.priority.desc()).limit(limit)).all()
    return [
        {
            "id": r.id,
            "query": r.query,
            "brand": r.brand,
            "locale": r.locale,
            "priority": r.priority,
            "enabled": r.enabled,
            "hit_count": r.hit_count,
            "last_run_at": r.last_run_at,
        }
        for r in rows
    ]


@router.post("/jobs/discovery", response_model=JobTriggerOut)
def trigger_discovery(async_mode: bool = True, limit: int = 15, db: Session = Depends(get_db)):
    if async_mode:
        try:
            from app.workers.tasks import task_discovery_batch

            async_result = task_discovery_batch.delay(limit=limit)
            return JobTriggerOut(ok=True, job="discovery", task_id=async_result.id)
        except Exception:
            # fallback sync if redis/celery down
            result = run_discovery_batch(db, limit=limit)
            return JobTriggerOut(ok=True, job="discovery", result=result)
    result = run_discovery_batch(db, limit=limit)
    return JobTriggerOut(ok=True, job="discovery", result=result)


@router.post("/jobs/crawl", response_model=JobTriggerOut)
def trigger_crawl(async_mode: bool = True, limit: int = 25, db: Session = Depends(get_db)):
    if async_mode:
        try:
            from app.workers.tasks import task_crawl_batch

            async_result = task_crawl_batch.delay(limit=limit)
            return JobTriggerOut(ok=True, job="crawl", task_id=async_result.id)
        except Exception:
            result = run_crawl_batch(db, limit=limit)
            return JobTriggerOut(ok=True, job="crawl", result=result)
    result = run_crawl_batch(db, limit=limit)
    return JobTriggerOut(ok=True, job="crawl", result=result)


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db), limit: int = 30):
    rows = db.scalars(select(JobRun).order_by(JobRun.id.desc()).limit(limit)).all()
    return [
        {
            "id": r.id,
            "job_type": r.job_type,
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "stats": r.stats,
            "error": r.error,
        }
        for r in rows
    ]


@router.post("/jobs/auto", response_model=JobTriggerOut)
def trigger_auto_pipeline(
    query_limit: int = 20,
    dive_limit: int = 8,
    db: Session = Depends(get_db),
):
    """One-click: drain WA queue → blitz → crawl → reharvest → dedup → dive."""
    from app.services.whatsapp_harvest import run_whatsapp_blitz, whatsapp_count
    from app.services.reharvest import reharvest_pending_snippets
    from app.services.browser_dive import run_browser_deep_dive
    from app.services.quality import dedup_whatsapp_variants
    from app.services.drain import drain_wa_pending
    from app.services.alerts import evaluate_alerts

    before = whatsapp_count(db)
    from app.services.offline_harvest import offline_harvest_all

    offline = offline_harvest_all(db, limit=5000)
    drain = drain_wa_pending(db, limit=80, fetch_pages=False)
    blitz = run_whatsapp_blitz(db, query_limit=max(query_limit, 40), workers=8)
    crawl = run_crawl_batch(db, limit=40)
    reharvest = reharvest_pending_snippets(db, limit=600)
    dedup = dedup_whatsapp_variants(db)
    dive = {"skipped": True}
    try:
        dive = run_browser_deep_dive(db, limit=dive_limit, yupoo_only=True, workers=2)
    except Exception as exc:
        dive = {"error": str(exc)[:400]}
    alerts = evaluate_alerts(db)
    after = whatsapp_count(db)
    return JobTriggerOut(
        ok=True,
        job="auto",
        result={
            "whatsapp_before": before,
            "whatsapp_after": after,
            "whatsapp_gained": max(0, after - before),
            "whatsapp_target": 10000,
            "offline": offline,
            "drain": drain,
            "blitz": blitz,
            "crawl": crawl,
            "reharvest": reharvest,
            "dedup": dedup,
            "browser_dive": dive,
            "alerts": alerts.get("alerts"),
        },
    )


@router.post("/jobs/browser-dive", response_model=JobTriggerOut)
def trigger_browser_dive(
    limit: int = 15,
    yupoo_only: bool = True,
    workers: int = 3,
    db: Session = Depends(get_db),
):
    from app.services.browser_dive import run_browser_deep_dive

    result = run_browser_deep_dive(db, limit=limit, yupoo_only=yupoo_only, workers=workers)
    return JobTriggerOut(ok=True, job="browser_deep_dive", result=result)


@router.post("/jobs/dedup", response_model=JobTriggerOut)
def trigger_dedup(db: Session = Depends(get_db)):
    from app.services.quality import dedup_whatsapp_variants

    return JobTriggerOut(ok=True, job="dedup", result=dedup_whatsapp_variants(db))


@router.post("/jobs/drain", response_model=JobTriggerOut)
def trigger_drain(limit: int = 60, fetch_pages: bool = False, db: Session = Depends(get_db)):
    from app.services.drain import drain_wa_pending

    return JobTriggerOut(
        ok=True,
        job="drain_wa",
        result=drain_wa_pending(db, limit=limit, fetch_pages=fetch_pages),
    )


@router.post("/jobs/offline-harvest", response_model=JobTriggerOut)
def trigger_offline_harvest(limit: int = 5000, db: Session = Depends(get_db)):
    from app.services.offline_harvest import offline_harvest_all

    return JobTriggerOut(ok=True, job="offline_harvest", result=offline_harvest_all(db, limit=limit))


@router.post("/jobs/whatsapp-verify", response_model=JobTriggerOut)
def trigger_whatsapp_verify(
    background_tasks: BackgroundTasks,
    limit: int = 40,
    delay_ms: int = 4000,
):
    """Start Baileys verify in background — does not block the API."""
    from app.db.session import SessionLocal
    from app.services.wa_verify import auth_ready, run_whatsapp_verify

    if not auth_ready():
        return JobTriggerOut(
            ok=False,
            job="whatsapp_verify",
            result={
                "ok": False,
                "error": "WhatsApp session manquante — ./scripts/whatsapp-login.sh",
                "auth_ready": False,
            },
        )

    def _run():
        s = SessionLocal()
        try:
            run_whatsapp_verify(s, limit=limit, delay_ms=delay_ms)
        finally:
            s.close()

    background_tasks.add_task(_run)
    return JobTriggerOut(
        ok=True,
        job="whatsapp_verify",
        result={"ok": True, "started": True, "limit": limit, "message": "vérif lancée en arrière-plan"},
    )


@router.get("/whatsapp-verify/status")
def whatsapp_verify_status():
    from app.services.wa_verify import auth_ready, WA_DIR

    return {
        "auth_ready": auth_ready(),
        "tool_dir": str(WA_DIR),
        "login_hint": "./scripts/whatsapp-login.sh",
        "verify_hint": "./scripts/whatsapp-verify.sh 40",
    }


@router.post("/jobs/yupoo-expand", response_model=JobTriggerOut)
def trigger_yupoo_expand(seed_limit: int = 35, db: Session = Depends(get_db)):
    from app.services.yupoo_expand import run_yupoo_expand

    return JobTriggerOut(ok=True, job="yupoo_expand", result=run_yupoo_expand(db, seed_limit=seed_limit))


@router.post("/jobs/yupoo-raw", response_model=JobTriggerOut)
def trigger_yupoo_raw(limit: int = 50, db: Session = Depends(get_db)):
    from app.services.yupoo_raw import run_yupoo_raw_crawl

    return JobTriggerOut(ok=True, job="yupoo_raw_crawl", result=run_yupoo_raw_crawl(db, limit=limit, workers=6))


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    from app.services.alerts import evaluate_alerts

    return evaluate_alerts(db)


@router.get("/autopilot")
def autopilot_status(db: Session = Depends(get_db)):
    from app.services.autopilot import status_snapshot
    from app.services.wa_verify import auth_ready
    from app.services.whatsapp_harvest import whatsapp_count

    snap = status_snapshot()
    snap["whatsapp"] = whatsapp_count(db)
    snap["wa_auth"] = auth_ready()
    return snap


@router.post("/autopilot")
def autopilot_set(enabled: bool = True, verify_wa: bool = True):
    from app.services.autopilot import set_enabled

    return set_enabled(enabled, verify_wa=verify_wa)


@router.post("/autopilot/tick", response_model=JobTriggerOut)
def autopilot_tick(background_tasks: BackgroundTasks, verify: bool = False, boost: bool = True):
    """Force one autopilot cycle in background."""
    from app.db.session import SessionLocal
    from app.services.autopilot import run_cycle

    def _run():
        s = SessionLocal()
        try:
            run_cycle(s, do_verify=verify, boost=boost)
        finally:
            s.close()

    background_tasks.add_task(_run)
    return JobTriggerOut(ok=True, job="autopilot_tick", result={"started": True, "verify": verify, "boost": boost})


@router.post("/boost", response_model=JobTriggerOut)
def trigger_boost(background_tasks: BackgroundTasks, rounds: int = 1):
    """Ultra-fast WA discovery wave (peak-hour path: blitz 40×8 + Yupoo raw)."""
    from app.db.session import SessionLocal
    from app.services.autopilot import run_cycle
    from app.services.engine_state import clear_cooldown

    clear_cooldown()
    rounds = max(1, min(int(rounds), 5))

    def _run():
        for _ in range(rounds):
            s = SessionLocal()
            try:
                run_cycle(s, do_verify=False, boost=True)
            finally:
                s.close()

    background_tasks.add_task(_run)
    return JobTriggerOut(ok=True, job="boost", result={"started": True, "rounds": rounds})


@router.get("/export/case-pack")
def export_case_pack(
    brand: str | None = None,
    lead_type: str | None = None,
    min_living: float = 0,
    db: Session = Depends(get_db),
):
    from app.services.legal_export import build_case_pack_zip

    data = build_case_pack_zip(db, brand=brand, lead_type=lead_type, min_living=min_living)
    name = f"wareach_case_{brand or 'all'}_{lead_type or 'all'}.zip"
    return StreamingResponse(
        iter([data]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.post("/jobs/whatsapp-blitz", response_model=JobTriggerOut)
def trigger_whatsapp_blitz(
    query_limit: int = 40,
    workers: int = 8,
    db: Session = Depends(get_db),
):
    from app.services.whatsapp_harvest import run_whatsapp_blitz

    result = run_whatsapp_blitz(db, query_limit=query_limit, workers=workers)
    return JobTriggerOut(ok=True, job="whatsapp_blitz", result=result)


@router.get("/export/whatsapp-csv")
def export_whatsapp_csv(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Contact)
        .where(Contact.contact_type.in_(["whatsapp", "wechat", "telegram"]))
        .order_by(Contact.verify_status.asc(), Contact.last_seen_at.desc())
    ).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "type",
            "value",
            "verify_status",
            "open_url",
            "brand",
            "source_url",
            "supplier_id",
            "seen_count",
            "verified_at",
            "first_seen",
            "last_seen",
        ]
    )
    for c in rows:
        w.writerow(
            [
                c.contact_type,
                c.normalized_value,
                getattr(c, "verify_status", None) or "unverified",
                _contact_open_url(c) or "",
                c.brand_context,
                c.source_url,
                c.supplier_id,
                c.seen_count,
                c.verified_at.isoformat() if getattr(c, "verified_at", None) else "",
                c.first_seen_at.isoformat() if c.first_seen_at else "",
                c.last_seen_at.isoformat() if c.last_seen_at else "",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wareach_contacts_verify.csv"},
    )


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    suppliers = db.scalars(select(Supplier).order_by(Supplier.risk_score.desc())).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "id",
            "canonical_key",
            "display_name",
            "lead_type",
            "quality_tier",
            "platform",
            "url",
            "brands",
            "groups",
            "geo_clusters",
            "risk_score",
            "priority_score",
            "status",
            "whatsapp",
            "wechat",
            "telegram",
            "region",
            "first_seen",
            "last_seen",
        ]
    )
    for s in suppliers:
        contacts = db.scalars(select(Contact).where(Contact.supplier_id == s.id)).all()
        by_type: dict[str, list[str]] = {}
        for c in contacts:
            by_type.setdefault(c.contact_type, []).append(c.normalized_value)
        w.writerow(
            [
                s.id,
                s.canonical_key,
                s.display_name,
                getattr(s, "lead_type", ""),
                getattr(s, "quality_tier", ""),
                s.primary_platform,
                s.primary_url,
                "|".join(s.brands or []),
                "|".join(getattr(s, "groups", None) or []),
                "|".join(getattr(s, "geo_clusters", None) or []),
                s.risk_score,
                getattr(s, "priority_score", 0),
                s.status,
                "|".join(by_type.get("whatsapp", [])),
                "|".join(by_type.get("wechat", [])),
                "|".join(by_type.get("telegram", [])),
                s.region_hint,
                s.first_seen_at.isoformat() if s.first_seen_at else "",
                s.last_seen_at.isoformat() if s.last_seen_at else "",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wareach_suppliers.csv"},
    )


@router.get("/doctor")
def doctor_cached(db: Session = Depends(get_db), refresh: bool = False):
    if not refresh:
        row = db.scalar(select(SystemMetric).where(SystemMetric.key == "agent_reach_doctor"))
        if row:
            return {"cached": True, "updated_at": row.updated_at, "data": row.value}
    data = run_doctor()
    row = db.scalar(select(SystemMetric).where(SystemMetric.key == "agent_reach_doctor"))
    if not row:
        row = SystemMetric(key="agent_reach_doctor", value=data)
        db.add(row)
    else:
        from app.services.pipeline import utcnow

        row.value = data
        row.updated_at = utcnow()
    db.commit()
    return {"cached": False, "data": data}
