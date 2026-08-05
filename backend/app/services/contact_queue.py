"""Contact queue CRM — found → queued → contacted → engaged | opted_out."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import ConsumerLead
from app.services.outreach_templates import render_template

logger = logging.getLogger(__name__)

VALID_STATUSES = {"found", "queued", "contacted", "engaged", "opted_out"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_queue(db: Session, *, limit: int = 50, offset: int = 0) -> list[ConsumerLead]:
    return list(
        db.scalars(
            select(ConsumerLead)
            .where(ConsumerLead.contact_status == "queued")
            .order_by(ConsumerLead.buyer_score.desc(), ConsumerLead.last_seen_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )


def enqueue_lead(db: Session, lead_id: int, *, note: str | None = None) -> ConsumerLead | None:
    lead = db.get(ConsumerLead, lead_id)
    if not lead:
        return None
    if lead.contact_status not in {"found", "queued"}:
        return lead
    lead.contact_status = "queued"
    meta = dict(lead.meta or {})
    meta["queued_at"] = utcnow().isoformat()
    if note:
        notes = list(meta.get("ops_notes") or [])
        notes.append({"at": utcnow().isoformat(), "note": note[:500]})
        meta["ops_notes"] = notes[-20:]
    # Attach outreach template preview
    brands = lead.brands_interest or []
    brand = brands[0] if brands else "luxe"
    meta["outreach_preview"] = render_template(
        lead.platform,
        brand=brand.replace("_", " ").title(),
    )
    lead.meta = meta
    lead.last_seen_at = utcnow()
    db.commit()
    db.refresh(lead)
    return lead


def update_contact_status(
    db: Session,
    lead_id: int,
    *,
    status: str,
    note: str | None = None,
    contact_method: str | None = None,
) -> ConsumerLead | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    lead = db.get(ConsumerLead, lead_id)
    if not lead:
        return None
    lead.contact_status = status
    if contact_method:
        lead.contact_method = contact_method[:64]
    meta = dict(lead.meta or {})
    meta[f"status_{status}_at"] = utcnow().isoformat()
    if note:
        notes = list(meta.get("ops_notes") or [])
        notes.append({"at": utcnow().isoformat(), "status": status, "note": note[:500]})
        meta["ops_notes"] = notes[-20:]
    lead.meta = meta
    lead.last_seen_at = utcnow()
    db.commit()
    db.refresh(lead)
    return lead


def auto_enqueue_qualified(db: Session, *, limit: int = 40) -> int:
    """Move eligible FR leads from found → queued."""
    from app.services.consumer_enrich import QUEUE_SCORE_MIN, is_queue_eligible

    rows = list(
        db.scalars(
            select(ConsumerLead)
            .where(ConsumerLead.contact_status == "found")
            .where(ConsumerLead.buyer_score >= QUEUE_SCORE_MIN)
            .order_by(ConsumerLead.buyer_score.desc())
            .limit(limit)
        )
    )
    n = 0
    for lead in rows:
        if is_queue_eligible(lead):
            enqueue_lead(db, lead.id)
            n += 1
    return n


def queue_stats(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(ConsumerLead.contact_status, func.count()).group_by(ConsumerLead.contact_status)
    ).all()
    return {str(k): int(v) for k, v in rows}


def export_consumers(
    db: Session,
    *,
    fmt: str = "csv",
    status: str | None = None,
    platform: str | None = None,
    min_score: float = 0,
    limit: int = 2000,
) -> tuple[str, str, bytes]:
    """Return (media_type, filename, body)."""
    stmt = select(ConsumerLead).order_by(ConsumerLead.buyer_score.desc()).limit(limit)
    if status:
        stmt = stmt.where(ConsumerLead.contact_status == status)
    if platform:
        stmt = stmt.where(ConsumerLead.platform == platform)
    if min_score > 0:
        stmt = stmt.where(ConsumerLead.buyer_score >= min_score)
    rows = list(db.scalars(stmt))

    if fmt == "json":
        payload: list[dict[str, Any]] = []
        for r in rows:
            payload.append(
                {
                    "id": r.id,
                    "platform": r.platform,
                    "handle": r.handle,
                    "display_name": r.display_name,
                    "profile_url": r.profile_url,
                    "country_hint": r.country_hint,
                    "brands_interest": r.brands_interest,
                    "buyer_score": r.buyer_score,
                    "lead_role": r.lead_role,
                    "contact_status": r.contact_status,
                    "contact_method": r.contact_method,
                    "source_url": r.source_url,
                    "snippet": r.snippet,
                    "seen_count": r.seen_count,
                }
            )
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        return "application/json", "consumers.json", body

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "id",
            "platform",
            "handle",
            "display_name",
            "profile_url",
            "country",
            "brands",
            "buyer_score",
            "lead_role",
            "contact_status",
            "contact_method",
            "source_url",
            "snippet",
            "seen_count",
        ]
    )
    for r in rows:
        brands = r.brands_interest or []
        w.writerow(
            [
                r.id,
                r.platform,
                r.handle,
                r.display_name or "",
                r.profile_url or "",
                r.country_hint or "",
                ";".join(brands) if isinstance(brands, list) else brands,
                r.buyer_score,
                r.lead_role,
                r.contact_status,
                r.contact_method or "",
                r.source_url or "",
                (r.snippet or "")[:300],
                r.seen_count,
            ]
        )
    return "text/csv", "consumers.csv", buf.getvalue().encode("utf-8")
