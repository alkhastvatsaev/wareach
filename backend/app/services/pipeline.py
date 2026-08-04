"""Persist discovery + crawl results into Postgres with dedup."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Contact, DiscoveredUrl, Evidence, JobRun, SearchQuery, Supplier, SystemMetric
from app.services.discovery import SearchHit, discover, fetch_page_content
from app.services.extractor import (
    domain_of,
    extract_all,
    supplier_key_from_contacts,
    url_hash,
)

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


def upsert_discovered_urls(
    db: Session,
    hits: list[SearchHit],
    source_query: str,
    brand_hint: str | None,
    priority: int = 100,
) -> int:
    added = 0
    for hit in hits:
        h = url_hash(hit.url)
        existing = db.scalar(select(DiscoveredUrl).where(DiscoveredUrl.url_hash == h))
        if existing:
            continue
        db.add(
            DiscoveredUrl(
                url=hit.url,
                url_hash=h,
                domain=domain_of(hit.url),
                title=hit.title,
                snippet=hit.snippet,
                source_query=source_query,
                brand_hint=brand_hint,
                priority=priority,
                status="pending",
            )
        )
        try:
            db.commit()
            added += 1
        except IntegrityError:
            db.rollback()
    return added


def merge_supplier_from_extraction(
    db: Session,
    *,
    url: str,
    title: str | None,
    text: str,
    brand_hint: str | None,
) -> dict:
    result = extract_all(text, source_url=url)
    if brand_hint and brand_hint not in result.brands:
        result.brands.append(brand_hint)

    # Also extract from title/snippet-like head
    domain = domain_of(url)
    key = supplier_key_from_contacts(result.contacts, domain)
    if not key:
        return {"supplier_id": None, "contacts": 0, "risk": result.risk_score, "brands": result.brands}

    # Skip creating suppliers from media/noise unless a WhatsApp was extracted
    if result.lead_type == "noise_media":
        if not any(c.contact_type == "whatsapp" for c in result.contacts):
            return {
                "supplier_id": None,
                "contacts": 0,
                "risk": result.risk_score,
                "brands": result.brands,
                "skipped": "noise_media",
            }

    has_direct = any(c.contact_type in {"whatsapp", "wechat", "telegram", "phone", "qq"} for c in result.contacts)
    if not has_direct and result.lead_type in {"unknown"}:
        return {"supplier_id": None, "contacts": 0, "risk": result.risk_score, "brands": result.brands, "skipped": "no_contact"}

    supplier = db.scalar(select(Supplier).where(Supplier.canonical_key == key))
    if not supplier:
        name = None
        for c in result.contacts:
            if c.contact_type in {"whatsapp", "wechat", "telegram"}:
                name = f"{c.contact_type}:{c.normalized_value}"
                break
        region = "China"
        if result.geo_clusters:
            region = f"China/{','.join(result.geo_clusters[:2])}"
        supplier = Supplier(
            canonical_key=key,
            display_name=name or domain,
            primary_platform=_platform_from_domain(domain),
            primary_url=url,
            region_hint=region,
            brands=result.brands,
            groups=result.groups,
            lead_type=result.lead_type,
            quality_tier=result.quality_tier,
            geo_clusters=result.geo_clusters,
            signals=result.signals[:40],
            risk_score=result.risk_score,
            priority_score=result.priority_score,
            confidence=min(1.0, result.risk_score / 100.0),
            status="new",
        )
        db.add(supplier)
        db.flush()
    else:
        brands = set(supplier.brands or []) | set(result.brands)
        supplier.brands = list(brands)
        groups = set(getattr(supplier, "groups", None) or []) | set(result.groups)
        supplier.groups = list(groups)
        geos = set(getattr(supplier, "geo_clusters", None) or []) | set(result.geo_clusters)
        supplier.geo_clusters = list(geos)
        sigs = set(getattr(supplier, "signals", None) or []) | set(result.signals)
        supplier.signals = list(sigs)[:60]
        # Prefer stronger classifications
        tier_rank = {"god_tier": 4, "high": 3, "mid": 2, "low": 1, "unknown": 0}
        if tier_rank.get(result.quality_tier, 0) >= tier_rank.get(supplier.quality_tier or "unknown", 0):
            supplier.quality_tier = result.quality_tier
        type_rank = {
            "jewelry_factory": 5,
            "hq_replica": 4,
            "gray_jeweler": 3,
            "jewelry_oem": 3,
            "multi_reseller": 2,
            "unknown": 0,
        }
        if type_rank.get(result.lead_type, 0) >= type_rank.get(supplier.lead_type or "unknown", 0):
            supplier.lead_type = result.lead_type
        supplier.risk_score = max(supplier.risk_score or 0, result.risk_score)
        supplier.priority_score = max(getattr(supplier, "priority_score", 0) or 0, result.priority_score)
        supplier.confidence = max(supplier.confidence or 0, min(1.0, result.risk_score / 100.0))
        supplier.last_seen_at = utcnow()
        if not supplier.primary_url:
            supplier.primary_url = url

    contact_count = 0
    for c in result.contacts:
        if c.contact_type == "website":
            continue
        existing = db.scalar(
            select(Contact).where(
                Contact.contact_type == c.contact_type,
                Contact.normalized_value == c.normalized_value,
            )
        )
        if existing:
            existing.last_seen_at = utcnow()
            existing.seen_count = (existing.seen_count or 1) + 1
            if not existing.supplier_id:
                existing.supplier_id = supplier.id
            contact_count += 1
            continue
        db.add(
            Contact(
                supplier_id=supplier.id,
                contact_type=c.contact_type,
                raw_value=c.raw_value[:500],
                normalized_value=c.normalized_value[:500],
                source_url=url,
                brand_context=brand_hint,
            )
        )
        contact_count += 1

    excerpt = text[:1200]
    db.add(
        Evidence(
            supplier_id=supplier.id,
            url=url,
            title=title,
            excerpt=excerpt,
            brands_detected=result.brands,
            raw_meta={
                "signals": result.signals,
                "hq_signals": result.hq_signals,
                "jewelry_signals": result.jewelry_signals,
                "lead_type": result.lead_type,
                "quality_tier": result.quality_tier,
                "geo_clusters": result.geo_clusters,
                "groups": result.groups,
                "risk": result.risk_score,
                "priority": result.priority_score,
            },
        )
    )
    supplier.evidence_count = (supplier.evidence_count or 0) + 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Race: another worker inserted the same contact — re-count existing
        contact_count = 0
        for c in result.contacts:
            if c.contact_type == "website":
                continue
            existing = db.scalar(
                select(Contact).where(
                    Contact.contact_type == c.contact_type,
                    Contact.normalized_value == c.normalized_value,
                )
            )
            if existing:
                existing.last_seen_at = utcnow()
                existing.seen_count = (existing.seen_count or 1) + 1
                contact_count += 1
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        return {
            "supplier_id": supplier.id if supplier else None,
            "contacts": contact_count,
            "risk": result.risk_score,
            "priority": result.priority_score,
            "brands": result.brands,
            "lead_type": result.lead_type,
            "quality_tier": result.quality_tier,
            "canonical_key": key,
            "deduped": True,
        }
    return {
        "supplier_id": supplier.id,
        "contacts": contact_count,
        "risk": result.risk_score,
        "priority": result.priority_score,
        "brands": result.brands,
        "lead_type": result.lead_type,
        "quality_tier": result.quality_tier,
        "canonical_key": key,
    }


def _platform_from_domain(domain: str) -> str:
    d = (domain or "").lower()
    if "yupoo" in d:
        return "yupoo"
    if "weidian" in d or "wsxc" in d:
        return "weidian"
    if "dhgate" in d:
        return "dhgate"
    if "made-in-china" in d:
        return "made-in-china"
    if "telegram" in d or "t.me" in d or "tgstat" in d:
        return "telegram"
    if "taobao" in d or "1688" in d:
        return "alibaba_ecosystem"
    return "website"


def run_discovery_batch(db: Session, limit: int = 20) -> dict:
    job = JobRun(job_type="discovery", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    q = (
        select(SearchQuery)
        .where(SearchQuery.enabled.is_(True))
        .order_by(SearchQuery.last_run_at.nullsfirst(), SearchQuery.priority.desc())
        .limit(limit)
    )
    queries = list(db.scalars(q))
    urls_added = 0
    hits_total = 0
    errors = 0

    for sq in queries:
        try:
            hits = discover(sq.query)
            hits_total += len(hits)
            urls_added += upsert_discovered_urls(db, hits, sq.query, sq.brand, sq.priority)
            sq.last_run_at = utcnow()
            sq.hit_count = (sq.hit_count or 0) + len(hits)
            db.commit()
        except Exception as exc:
            errors += 1
            logger.exception("discovery query failed: %s", sq.query)
            db.rollback()

    job.status = "done"
    job.finished_at = utcnow()
    job.stats = {
        "queries": len(queries),
        "hits": hits_total,
        "urls_added": urls_added,
        "errors": errors,
    }
    db.commit()
    return job.stats


def run_crawl_batch(db: Session, limit: int = 30) -> dict:
    job = JobRun(job_type="crawl", status="running", stats={})
    db.add(job)
    db.commit()

    candidates = list(
        db.scalars(
            select(DiscoveredUrl)
            .where(DiscoveredUrl.status.in_(["pending", "failed"]))
            .where(DiscoveredUrl.fail_count < 5)
            .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.discovered_at.asc())
            .limit(limit * 5)
        )
    )

    def crawl_score(row: DiscoveredUrl) -> int:
        blob = f"{row.title or ''} {row.snippet or ''}".lower()
        s = int(row.priority or 0)
        if any(x in blob for x in ["whatsapp", "+86", "8613", "8615", "8618", "wa.me"]):
            s += 500
        if "yupoo" in (row.domain or "") or "yupoo" in (row.url or "").lower():
            s += 200
        if any(x in (row.domain or "") for x in ["weidian", "wsxc", "1688"]):
            s += 80
        return s

    rows = sorted(candidates, key=crawl_score, reverse=True)[:limit]

    crawled = 0
    suppliers_touched = 0
    contacts = 0
    failed = 0

    for row in rows:
        # Skip known media noise early
        if any(
            x in (row.domain or "")
            for x in ["thepaper", "36kr", "qq.com", "zhihu", "baidu.com", "wikipedia"]
        ):
            row.status = "ignored"
            db.commit()
            continue
        row.status = "crawling"
        db.commit()
        try:
            # Prefer snippet+title first for quick contact extraction, then full page
            seed_text = "\n".join(filter(None, [row.title, row.snippet, row.url]))
            page = fetch_page_content(row.url)
            text = f"{seed_text}\n{page}"
            info = merge_supplier_from_extraction(
                db,
                url=row.url,
                title=row.title,
                text=text,
                brand_hint=row.brand_hint,
            )
            row.status = "done"
            row.crawled_at = utcnow()
            row.last_error = None
            crawled += 1
            if info.get("supplier_id"):
                suppliers_touched += 1
            contacts += info.get("contacts") or 0
            db.commit()
        except Exception as exc:
            failed += 1
            try:
                db.rollback()
            except Exception:
                pass
            # re-bind row after rollback
            row = db.get(DiscoveredUrl, row.id)
            if row:
                row.status = "failed"
                row.fail_count = (row.fail_count or 0) + 1
                row.last_error = str(exc)[:1000]
                try:
                    db.commit()
                except Exception:
                    db.rollback()
            logger.exception("crawl failed %s", getattr(row, "url", "?"))

    job.status = "done"
    job.finished_at = utcnow()
    job.stats = {
        "crawled": crawled,
        "failed": failed,
        "suppliers_touched": suppliers_touched,
        "contacts": contacts,
        "batch_size": len(rows),
    }
    db.commit()
    return job.stats


def stats_overview(db: Session) -> dict:
    def count_type(lead: str) -> int:
        return db.scalar(select(func.count()).select_from(Supplier).where(Supplier.lead_type == lead)) or 0

    def count_tier(tier: str) -> int:
        return db.scalar(select(func.count()).select_from(Supplier).where(Supplier.quality_tier == tier)) or 0

    from app.services.pace import contact_pace
    from app.services.engine_state import status as engine_cooldowns

    pace = contact_pace(db)
    # Read-only alerts snapshot (Celery writes); avoid commit on every /stats poll
    alert_row = db.scalar(select(SystemMetric).where(SystemMetric.key == "alerts"))
    alert_payload = (alert_row.value if alert_row else {}) or {}
    return {
        "suppliers": db.scalar(select(func.count()).select_from(Supplier)) or 0,
        "contacts": db.scalar(select(func.count()).select_from(Contact)) or 0,
        "whatsapp": pace["whatsapp"],
        "wechat": pace["wechat"],
        "urls_pending": db.scalar(
            select(func.count()).select_from(DiscoveredUrl).where(DiscoveredUrl.status == "pending")
        )
        or 0,
        "urls_done": db.scalar(
            select(func.count()).select_from(DiscoveredUrl).where(DiscoveredUrl.status == "done")
        )
        or 0,
        "urls_total": db.scalar(select(func.count()).select_from(DiscoveredUrl)) or 0,
        "queries": db.scalar(
            select(func.count()).select_from(SearchQuery).where(SearchQuery.enabled.is_(True))
        )
        or 0,
        "evidences": db.scalar(select(func.count()).select_from(Evidence)) or 0,
        "hq_replica": count_type("hq_replica"),
        "jewelry_factory": count_type("jewelry_factory"),
        "gray_jeweler": count_type("gray_jeweler"),
        "god_tier": count_tier("god_tier"),
        "high_tier": count_tier("high"),
        "whatsapp_target": 10000,
        "whatsapp_remaining": max(0, 10000 - pace["whatsapp"]),
        "daily_pace_needed": 1429,
        "wa_per_hour": pace["wa_per_hour"],
        "contacts_per_hour": pace["contacts_per_hour"],
        "eta_hours_to_10k_wa": pace["eta_hours_to_10k_wa"],
        "wa_new_24h": pace["wa_new_24h"],
        "wx_new_24h": pace["wx_new_24h"],
        "alert_count": len(alert_payload.get("alerts") or []),
        "top_alert": (alert_payload.get("alerts") or [{}])[0].get("message")
        if alert_payload.get("alerts")
        else None,
        "engines_cooling": engine_cooldowns(),
        "unverified": db.scalar(
            select(func.count())
            .select_from(Contact)
            .where(
                Contact.contact_type.in_(["whatsapp", "wechat"]),
                or_(Contact.verify_status == "unverified", Contact.verify_status.is_(None)),
            )
        )
        or 0,
        "reachable": db.scalar(
            select(func.count()).select_from(Contact).where(Contact.verify_status == "reachable")
        )
        or 0,
        "dead": db.scalar(select(func.count()).select_from(Contact).where(Contact.verify_status == "dead"))
        or 0,
    }
