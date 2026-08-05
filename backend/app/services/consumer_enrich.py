"""Enrich ConsumerLead profiles via free page reads + re-scoring."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ConsumerLead, JobRun
from app.services.demand_discovery import detect_brands, score_consumer_text
from app.services.free_search import read_page_free

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
TG_RE = re.compile(r"(?:t\.me/|telegram\.me/|@)([A-Za-z0-9_]{4,32})")
DISCORD_TAG_RE = re.compile(r"(?:discord(?:\.gg|\.com/invite)/([A-Za-z0-9\-]+)|@?([A-Za-z0-9_]{2,32})#\d{4})")
WA_RE = re.compile(r"(?:wa\.me/|whatsapp\.com/send\?phone=|whatsapp[:\s]*)(\+?\d{10,15})", re.I)

# Qualification threshold for contact queue (plan: score >= 0.4 → map to 40/100 scale)
QUEUE_SCORE_MIN = 40.0


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def extract_contacts(text: str) -> dict:
    emails = list(dict.fromkeys(EMAIL_RE.findall(text or "")))[:5]
    tgs = []
    for m in TG_RE.finditer(text or ""):
        h = m.group(1)
        if h.lower() not in {"channel", "joinchat", "share", "addstickers"}:
            tgs.append(h)
    tgs = list(dict.fromkeys(tgs))[:5]
    discord = []
    for m in DISCORD_TAG_RE.finditer(text or ""):
        discord.append(m.group(1) or m.group(2))
    discord = list(dict.fromkeys(d for d in discord if d))[:5]
    was = list(dict.fromkeys(WA_RE.findall(text or "")))[:3]
    return {
        "emails": emails,
        "telegram_handles": tgs,
        "discord_tags": discord,
        "whatsapp": was,
    }


def enrich_lead(db: Session, lead: ConsumerLead) -> bool:
    """Read source_url / profile_url, update score, role, brands, contact hints."""
    url = lead.source_url or lead.profile_url
    if not url or not str(url).startswith("http"):
        return False

    meta = dict(lead.meta or {})
    if meta.get("enriched"):
        return False

    page = read_page_free(url, max_chars=15000)
    if not page or len(page) < 60:
        meta["enriched"] = True
        meta["enrich_empty"] = True
        lead.meta = meta
        db.commit()
        return False

    blob = f"{lead.snippet or ''}\n{page[:8000]}"
    score, role, country = score_consumer_text(blob)
    brands = detect_brands(blob)
    contacts = extract_contacts(page)

    lead.buyer_score = max(float(lead.buyer_score or 0), float(score))
    if role != "unknown" and (lead.lead_role in {None, "unknown"} or score > float(lead.buyer_score or 0) * 0.9):
        lead.lead_role = role
    if country and not lead.country_hint:
        lead.country_hint = country
    if country == "FR":
        lead.language = "fr"
    if brands:
        lead.brands_interest = list(dict.fromkeys((lead.brands_interest or []) + brands))
    if len(page) > len(lead.snippet or ""):
        lead.snippet = (lead.snippet or page[:1500])[:2000]

    # Prefer a concrete contact method when found
    if contacts["telegram_handles"] and not lead.contact_method:
        lead.contact_method = f"telegram:@{contacts['telegram_handles'][0]}"
    elif contacts["emails"] and not lead.contact_method:
        lead.contact_method = f"email:{contacts['emails'][0]}"
    elif contacts["discord_tags"] and not lead.contact_method:
        lead.contact_method = f"discord:{contacts['discord_tags'][0]}"

    meta["enriched"] = True
    meta["enriched_at"] = utcnow().isoformat()
    meta["extracted_contacts"] = contacts
    lead.meta = meta
    lead.last_seen_at = utcnow()
    db.commit()
    return True


def enrich_pending(db: Session, *, limit: int = 25) -> dict:
    """Enrich leads that have a source URL and are not yet enriched."""
    job = JobRun(job_type="consumer_enrich", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    rows = list(
        db.scalars(
            select(ConsumerLead)
            .where(ConsumerLead.source_url.isnot(None))
            .order_by(ConsumerLead.buyer_score.desc(), ConsumerLead.last_seen_at.desc())
            .limit(limit * 3)
        )
    )
    # Filter not-yet-enriched in Python (JSON meta)
    pending = [r for r in rows if not (r.meta or {}).get("enriched")][:limit]

    enriched = 0
    skipped = 0
    for lead in pending:
        try:
            ok = enrich_lead(db, lead)
            enriched += int(ok)
            skipped += int(not ok)
        except Exception:
            logger.debug("enrich failed for lead %s", lead.id, exc_info=True)
            skipped += 1

    # Auto-queue qualified FR buyers
    from app.services.contact_queue import auto_enqueue_qualified

    queued = auto_enqueue_qualified(db)

    stats = {
        "candidates": len(pending),
        "enriched": enriched,
        "skipped": skipped,
        "auto_queued": queued,
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("consumer_enrich done: %s", stats)
    return stats


def is_queue_eligible(lead: ConsumerLead) -> bool:
    """Plan: buyer_score >= 0.4 (40/100) and country_hint == FR."""
    if float(lead.buyer_score or 0) < QUEUE_SCORE_MIN:
        return False
    if (lead.country_hint or "").upper() != "FR":
        # Also allow strong buyers without country if role is buyer and score high
        if lead.lead_role == "buyer" and float(lead.buyer_score or 0) >= 55:
            return True
        return False
    return lead.contact_status == "found"
