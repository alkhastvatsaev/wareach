"""Parallel raw crawl of pending Yupoo URLs — skip Jina, extract WA from HTML."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import DiscoveredUrl, JobRun
from app.services.pipeline import merge_supplier_from_extraction, utcnow
from app.services.whatsapp_harvest import whatsapp_count

logger = logging.getLogger(__name__)


def _raw_get(url: str) -> tuple[str, str | None]:
    try:
        with httpx.Client(timeout=22, follow_redirects=True) as client:
            r = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            if r.status_code >= 400:
                return "", f"http_{r.status_code}"
            return r.text[:200_000], None
    except Exception as exc:
        return "", str(exc)[:200]


def run_yupoo_raw_crawl(db: Session, *, limit: int = 60, workers: int = 6) -> dict:
    before = whatsapp_count(db)
    job = JobRun(job_type="yupoo_raw_crawl", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    candidates = list(
        db.scalars(
            select(DiscoveredUrl)
            .where(DiscoveredUrl.status.in_(["pending", "failed"]))
            .where(DiscoveredUrl.fail_count < 4)
            .where(DiscoveredUrl.url.ilike("%yupoo%"))
            .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.id.desc())
            .limit(limit)
        )
    )

    for row in candidates:
        row.status = "crawling"
    db.commit()

    results: dict[int, tuple[str, str | None]] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
        futs = {pool.submit(_raw_get, row.url): row.id for row in candidates}
        for fut in as_completed(futs):
            rid = futs[fut]
            try:
                results[rid] = fut.result()
            except Exception as exc:
                results[rid] = ("", str(exc)[:200])

    crawled = failed = contacts = 0
    by_id = {r.id: r for r in candidates}
    for rid, (html, err) in results.items():
        row = by_id[rid]
        if not html or len(html) < 60:
            failed += 1
            row.status = "failed"
            row.fail_count = (row.fail_count or 0) + 1
            row.last_error = err or "empty"
            continue
        seed = "\n".join(filter(None, [row.title, row.snippet, row.url]))
        info = merge_supplier_from_extraction(
            db,
            url=row.url,
            title=row.title,
            text=f"{seed}\n{html}",
            brand_hint=row.brand_hint,
        )
        contacts += int(info.get("contacts") or 0)
        row.status = "done"
        row.crawled_at = utcnow()
        row.last_error = None
        crawled += 1
    db.commit()

    after = whatsapp_count(db)
    stats = {
        "batch": len(candidates),
        "crawled": crawled,
        "failed": failed,
        "contacts_ops": contacts,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
        "workers": workers,
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("yupoo_raw_crawl done: %s", stats)
    return stats
