"""Re-harvest WhatsApp from already discovered URL titles/snippets (no API cost)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import DiscoveredUrl
from app.services.discovery import SearchHit
from app.services.whatsapp_harvest import harvest_hit_snippet, whatsapp_count


def reharvest_pending_snippets(db: Session, limit: int = 500) -> dict:
    before = whatsapp_count(db)
    rows = list(
        db.scalars(
            select(DiscoveredUrl)
            .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.id.desc())
            .limit(limit)
        )
    )
    gained_contacts = 0
    scanned = 0
    for row in rows:
        blob = f"{row.title or ''} {row.snippet or ''}"
        if not any(x in blob.lower() for x in ["whatsapp", "+86", "861"]):
            continue
        scanned += 1
        hit = SearchHit(url=row.url, title=row.title, snippet=row.snippet)
        gained_contacts += harvest_hit_snippet(db, hit, row.brand_hint)
    after = whatsapp_count(db)
    return {
        "scanned_with_signal": scanned,
        "contact_ops": gained_contacts,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
    }
