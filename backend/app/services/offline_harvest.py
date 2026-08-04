"""Offline harvest — extract WA/WeChat from stored URLs/titles/snippets (zero network)."""

from __future__ import annotations

import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import DiscoveredUrl, JobRun
from app.services.pipeline import merge_supplier_from_extraction, utcnow
from app.services.whatsapp_harvest import whatsapp_count

logger = logging.getLogger(__name__)

MOBILE_RE = re.compile(r"(?:whats?a?pp?)?(?:86)?(1[3-9]\d{9})", re.I)


def offline_harvest_all(db: Session, *, limit: int = 5000) -> dict:
    before = whatsapp_count(db)
    job = JobRun(job_type="offline_harvest", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    rows = list(db.scalars(select(DiscoveredUrl).order_by(DiscoveredUrl.id.desc()).limit(limit)))
    scanned = 0
    with_signal = 0
    contact_ops = 0

    for row in rows:
        scanned += 1
        blob = f"{row.title or ''}\n{row.snippet or ''}\n{row.url or ''}"
        low = blob.lower()
        interesting = (
            "yupoo" in low
            or "weidian" in low
            or "whatsapp" in low
            or "+86" in low
            or MOBILE_RE.search(blob)
        )
        if not interesting:
            continue
        with_signal += 1
        info = merge_supplier_from_extraction(
            db,
            url=row.url,
            title=row.title,
            text=blob,
            brand_hint=row.brand_hint,
        )
        contact_ops += int(info.get("contacts") or 0)

    after = whatsapp_count(db)
    stats = {
        "scanned": scanned,
        "with_signal": with_signal,
        "contact_ops": contact_ops,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("offline_harvest done: %s", stats)
    return stats
