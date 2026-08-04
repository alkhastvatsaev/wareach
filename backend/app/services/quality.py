"""Contact quality scoring + light dedup for WhatsApp/WeChat."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Contact, Supplier
from app.services.extractor import normalize_phone_cn


def living_score(contact: Contact, supplier: Supplier | None = None) -> float:
    """0–100 heuristic: format quality + signal strength (not live WhatsApp ping)."""
    score = 40.0
    v = contact.normalized_value or ""
    ctype = contact.contact_type

    if ctype == "whatsapp":
        digits = re.sub(r"\D", "", v)
        if digits.startswith("86") and len(digits) == 13:
            score += 25
        elif len(digits) >= 10:
            score += 10
        else:
            score -= 20
        if v.startswith("+86"):
            score += 10
    elif ctype == "wechat":
        if 4 <= len(v) <= 32 and re.match(r"^[\w\-]+$", v):
            score += 20
        else:
            score -= 10

    if (contact.seen_count or 1) >= 2:
        score += 8
    if (contact.seen_count or 1) >= 4:
        score += 7

    if contact.verify_status == "reachable":
        score += 25
    elif contact.verify_status == "dead":
        score -= 40
    elif contact.verify_status == "busy":
        score += 5

    if supplier:
        if supplier.lead_type in {"hq_replica", "jewelry_factory"}:
            score += 12
        if (supplier.quality_tier or "") in {"god_tier", "high"}:
            score += 10
        if supplier.primary_platform and "yupoo" in (supplier.primary_platform or ""):
            score += 5

    return max(0.0, min(100.0, score))


def canonicalize_whatsapp(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return normalize_phone_cn(digits) if digits else (value or "")


def dedup_whatsapp_variants(db: Session) -> dict:
    """
    Merge WhatsApp rows that normalize to the same +86… key.
    Keeps lowest id, bumps seen_count, deletes duplicates.
    """
    rows = list(
        db.scalars(select(Contact).where(Contact.contact_type == "whatsapp").order_by(Contact.id)).all()
    )
    by_key: dict[str, list[Contact]] = {}
    for c in rows:
        key = canonicalize_whatsapp(c.normalized_value)
        if not key:
            continue
        by_key.setdefault(key, []).append(c)

    merged = 0
    deleted = 0
    for key, group in by_key.items():
        if len(group) < 2:
            keep = group[0]
            if keep.normalized_value != key:
                # avoid unique clash if another row somehow holds key
                clash = db.scalar(
                    select(Contact).where(
                        Contact.contact_type == "whatsapp",
                        Contact.normalized_value == key,
                        Contact.id != keep.id,
                    )
                )
                if not clash:
                    keep.normalized_value = key
                    merged += 1
            continue
        # Prefer row already on canonical key, else lowest id
        group_sorted = sorted(group, key=lambda c: (0 if c.normalized_value == key else 1, c.id))
        keep = group_sorted[0]
        keep.normalized_value = key
        for dup in group_sorted[1:]:
            keep.seen_count = (keep.seen_count or 1) + (dup.seen_count or 1)
            if dup.verify_status == "reachable":
                keep.verify_status = "reachable"
            elif dup.verify_status == "dead" and keep.verify_status == "unverified":
                keep.verify_status = "dead"
            if dup.source_url and not keep.source_url:
                keep.source_url = dup.source_url
            if dup.brand_context and not keep.brand_context:
                keep.brand_context = dup.brand_context
            if not keep.supplier_id and dup.supplier_id:
                keep.supplier_id = dup.supplier_id
            db.delete(dup)
            deleted += 1
            merged += 1
    db.commit()
    return {"groups_checked": len(by_key), "merged_ops": merged, "deleted": deleted}


def score_unverified_batch(db: Session, limit: int = 200) -> list[dict]:
    rows = list(
        db.scalars(
            select(Contact)
            .where(Contact.contact_type.in_(["whatsapp", "wechat"]))
            .order_by(Contact.last_seen_at.desc())
            .limit(limit)
        ).all()
    )
    supplier_ids = {c.supplier_id for c in rows if c.supplier_id}
    suppliers = {}
    if supplier_ids:
        for s in db.scalars(select(Supplier).where(Supplier.id.in_(supplier_ids))).all():
            suppliers[s.id] = s
    out = []
    for c in rows:
        s = suppliers.get(c.supplier_id) if c.supplier_id else None
        out.append(
            {
                "id": c.id,
                "type": c.contact_type,
                "value": c.normalized_value,
                "living_score": living_score(c, s),
                "verify_status": c.verify_status or "unverified",
            }
        )
    out.sort(key=lambda x: x["living_score"], reverse=True)
    return out
