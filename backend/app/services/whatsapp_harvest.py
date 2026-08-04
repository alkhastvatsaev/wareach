"""High-volume China WhatsApp harvest — snippet-first, parallel Exa."""

from __future__ import annotations

import logging
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Contact, JobRun, SearchQuery
from app.services.discovery import SearchHit, discover
from app.services.pipeline import merge_supplier_from_extraction, upsert_discovered_urls, utcnow

logger = logging.getLogger(__name__)


def whatsapp_count(db: Session) -> int:
    return (
        db.scalar(select(func.count()).select_from(Contact).where(Contact.contact_type == "whatsapp"))
        or 0
    )


def harvest_hit_snippet(db: Session, hit: SearchHit, brand_hint: str | None) -> int:
    """Extract WhatsApp from title+snippet+URL without fetching the page (fast path)."""
    text = "\n".join(filter(None, [hit.title, hit.snippet, hit.url]))
    low = text.lower()
    url_l = (hit.url or "").lower()
    has_signal = any(
        x in low
        for x in [
            "whatsapp",
            "whats app",
            "+86",
            "8613",
            "8615",
            "8618",
            "8619",
            "wa:",
            "wa：",
            "wa.me",
            "微信",
        ]
    )
    # Yupoo hosts often encode mobile in subdomain (18613…bag.x.yupoo.com)
    has_host_mobile = bool(
        "yupoo" in url_l and re.search(r"(?:^|//|/)(?:whats?a?pp?)?(?:86)?1[3-9]\d{9}", url_l)
    )
    if not has_signal and not has_host_mobile:
        return 0
    info = merge_supplier_from_extraction(
        db,
        url=hit.url,
        title=hit.title,
        text=text,
        brand_hint=brand_hint,
    )
    return int(info.get("contacts") or 0)


def _discover_one(query: str) -> tuple[str, list[SearchHit]]:
    try:
        return query, discover(query)
    except Exception as exc:
        logger.warning("discover failed %s: %s", query[:80], exc)
        return query, []


def run_whatsapp_blitz(
    db: Session,
    *,
    query_limit: int = 40,
    workers: int = 8,
    prefer_categories: list[str] | None = None,
) -> dict:
    """
    Parallel discovery + sequential DB harvest.
    Yupoo titles often embed WhatsApp:+86… — we extract before crawling.
    """
    before = whatsapp_count(db)
    job = JobRun(job_type="whatsapp_blitz", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    prefer = prefer_categories or [
        "high_yield",
        "whatsapp_blitz",
        "b2b_china",
        "social",
        "hq_replica",
        "hq_replica_jewelry",
        "jewelry_factory",
        "general",
    ]

    stmt = (
        select(SearchQuery)
        .where(SearchQuery.enabled.is_(True))
        .order_by(SearchQuery.last_run_at.nullsfirst(), SearchQuery.priority.desc())
        .limit(query_limit * 4)
    )
    candidates = list(db.scalars(stmt))

    def score_q(sq: SearchQuery) -> int:
        s = 0
        if sq.category in prefer:
            s += 50 + (len(prefer) - prefer.index(sq.category)) * 5
        ql = (sq.query or "").lower()
        if "whatsapp" in ql or "+86" in ql:
            s += 40
        if "yupoo" in ql:
            s += 30
        s += int(sq.priority or 0)
        return s

    # Shuffle among top scorers so we don't burn the same queries every cycle
    ranked = sorted(candidates, key=score_q, reverse=True)[: max(query_limit * 2, query_limit)]
    random.shuffle(ranked)
    queries = ranked[:query_limit]
    query_map = {q.query: q for q in queries}

    discovered: list[tuple[SearchQuery, list[SearchHit]]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 10))) as pool:
        futs = {pool.submit(_discover_one, q.query): q for q in queries}
        for fut in as_completed(futs):
            qtext, hits = fut.result()
            sq = query_map.get(qtext)
            if sq is not None:
                discovered.append((sq, hits))

    hits_total = 0
    urls_added = 0
    snippet_contacts = 0
    wa_hits_with_signal = 0

    # Sequential DB writes (SQLite-safe)
    for sq, hits in discovered:
        hits_total += len(hits)
        urls_added += upsert_discovered_urls(
            db, hits, sq.query, sq.brand, max(sq.priority or 100, 200)
        )
        for hit in hits:
            blob = f"{hit.title or ''} {hit.snippet or ''}".lower()
            if any(x in blob for x in ["whatsapp", "+86", "8613", "8615", "8618", "8619"]):
                wa_hits_with_signal += 1
            snippet_contacts += harvest_hit_snippet(db, hit, sq.brand)
        sq.last_run_at = utcnow()
        sq.hit_count = (sq.hit_count or 0) + len(hits)
        db.commit()

    after = whatsapp_count(db)
    stats = {
        "queries": len(queries),
        "hits": hits_total,
        "urls_added": urls_added,
        "snippet_contacts": snippet_contacts,
        "hits_with_wa_signal": wa_hits_with_signal,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
        "whatsapp_target": 10000,
        "workers": workers,
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("whatsapp blitz done: %s", stats)
    return stats
