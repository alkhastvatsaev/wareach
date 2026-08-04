"""Pace / ETA metrics toward WhatsApp target."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Contact, JobRun


def contact_pace(db: Session, *, hours: int = 24, target: int = 10000) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    wa_now = (
        db.scalar(select(func.count()).select_from(Contact).where(Contact.contact_type == "whatsapp"))
        or 0
    )
    wx_now = (
        db.scalar(select(func.count()).select_from(Contact).where(Contact.contact_type == "wechat"))
        or 0
    )
    # New contacts in window (approx via first_seen)
    wa_new = (
        db.scalar(
            select(func.count())
            .select_from(Contact)
            .where(Contact.contact_type == "whatsapp", Contact.first_seen_at >= since)
        )
        or 0
    )
    wx_new = (
        db.scalar(
            select(func.count())
            .select_from(Contact)
            .where(Contact.contact_type == "wechat", Contact.first_seen_at >= since)
        )
        or 0
    )
    per_hour = round((wa_new + wx_new) / max(hours, 1), 2)
    remaining = max(0, target - (wa_now + wx_new * 0))  # target still WA-primary
    wa_remaining = max(0, target - wa_now)
    eta_hours = None
    if per_hour > 0 and wa_remaining > 0:
        # attribute pace mostly to WA if mixed
        wa_pace = wa_new / max(hours, 1)
        if wa_pace > 0:
            eta_hours = round(wa_remaining / wa_pace, 1)
        else:
            eta_hours = round(wa_remaining / max(per_hour, 0.01), 1)

    # Last blitz gains from job stats
    last = db.scalars(
        select(JobRun)
        .where(JobRun.job_type.in_(["whatsapp_blitz", "auto", "browser_deep_dive"]))
        .order_by(JobRun.id.desc())
        .limit(5)
    ).all()
    recent_gains = []
    for j in last:
        g = (j.stats or {}).get("whatsapp_gained")
        if g is not None:
            recent_gains.append(int(g))

    return {
        "whatsapp": wa_now,
        "wechat": wx_now,
        "wa_new_24h": wa_new,
        "wx_new_24h": wx_new,
        "contacts_per_hour": per_hour,
        "wa_per_hour": round(wa_new / max(hours, 1), 2),
        "eta_hours_to_10k_wa": eta_hours,
        "recent_job_gains": recent_gains,
        "on_track_daily": wa_new >= 1429 if hours >= 24 else None,
    }
