"""Drain pending URLs that already show WhatsApp/+86 in title/snippet — highest ROI."""

from __future__ import annotations

import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.entities import DiscoveredUrl, JobRun
from app.services.discovery import SearchHit, fetch_page_content
from app.services.pipeline import merge_supplier_from_extraction, utcnow
from app.services.whatsapp_harvest import harvest_hit_snippet, whatsapp_count

logger = logging.getLogger(__name__)


def _has_wa_signal(row: DiscoveredUrl) -> bool:
    blob = f"{row.title or ''} {row.snippet or ''} {row.url or ''}".lower()
    return any(x in blob for x in ["whatsapp", "+86", "8613", "8615", "8618", "8619", "wa.me", "wa："])


def drain_wa_pending(db: Session, *, limit: int = 80, fetch_pages: bool = False) -> dict:
    """
    1) Snippet-extract all pending WA-signal URLs (default: no page fetch — Jina-safe)
    2) Optionally fetch pages when fetch_pages=True
    """
    before = whatsapp_count(db)
    job = JobRun(job_type="drain_wa", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    # Prefer pending with WA signal; fall back to any yupoo pending
    rows = list(
        db.scalars(
            select(DiscoveredUrl)
            .where(DiscoveredUrl.status.in_(["pending", "failed"]))
            .where(DiscoveredUrl.fail_count < 5)
            .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.id.desc())
            .limit(limit * 4)
        )
    )
    rows = [
        r
        for r in rows
        if "bing" not in (r.domain or "").lower()
        and "google.com" not in (r.domain or "").lower()
        and "duckduckgo" not in (r.domain or "").lower()
    ]
    signal_rows = [r for r in rows if _has_wa_signal(r)][:limit]
    if len(signal_rows) < limit // 2:
        extra = [
            r
            for r in rows
            if r not in signal_rows
            and ("yupoo" in (r.domain or "") or "yupoo" in (r.url or "").lower())
        ]
        signal_rows.extend(extra[: max(0, limit - len(signal_rows))])

    snippet_ops = 0
    fetched = 0
    failed = 0
    contacts = 0

    for row in signal_rows:
        hit = SearchHit(url=row.url, title=row.title, snippet=row.snippet)
        try:
            snippet_ops += harvest_hit_snippet(db, hit, row.brand_hint)
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
            continue

        if not fetch_pages:
            # Avoid reprocessing the same pending URLs forever
            if row.status in {"pending", "failed"}:
                row.status = "done"
                row.crawled_at = utcnow()
                row.last_error = None
                try:
                    db.commit()
                except Exception:
                    db.rollback()
            continue
        # Skip heavy news domains
        if any(x in (row.domain or "") for x in ["thepaper", "36kr", "zhihu", "wikipedia", "qq.com"]):
            row.status = "ignored"
            try:
                db.commit()
            except Exception:
                db.rollback()
            continue

        row.status = "crawling"
        db.commit()
        try:
            seed = "\n".join(filter(None, [row.title, row.snippet, row.url]))
            page = fetch_page_content(row.url)
            text = f"{seed}\n{page}"
            info = merge_supplier_from_extraction(
                db, url=row.url, title=row.title, text=text, brand_hint=row.brand_hint
            )
            contacts += int(info.get("contacts") or 0)
            row.status = "done"
            row.crawled_at = utcnow()
            row.last_error = None
            fetched += 1
            db.commit()
        except Exception as exc:
            failed += 1
            try:
                db.rollback()
            except Exception:
                pass
            row = db.get(DiscoveredUrl, row.id)
            if row:
                row.status = "failed"
                row.fail_count = (row.fail_count or 0) + 1
                row.last_error = str(exc)[:800]
                try:
                    db.commit()
                except Exception:
                    db.rollback()

    after = whatsapp_count(db)
    stats = {
        "candidates": len(signal_rows),
        "snippet_ops": snippet_ops,
        "pages_fetched": fetched,
        "failed": failed,
        "contacts_ops": contacts,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("drain_wa done: %s", stats)
    return stats
