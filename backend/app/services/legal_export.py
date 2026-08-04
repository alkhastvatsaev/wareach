"""Legal case-file export — CSV pack for brand counsel / investigators."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Contact, Evidence, Supplier
from app.services.quality import living_score


def build_case_pack_zip(
    db: Session,
    *,
    brand: str | None = None,
    lead_type: str | None = None,
    min_living: float = 0,
) -> bytes:
    suppliers = list(db.scalars(select(Supplier).order_by(Supplier.priority_score.desc())).all())
    if brand:
        suppliers = [s for s in suppliers if brand in (s.brands or [])]
    if lead_type:
        suppliers = [s for s in suppliers if (s.lead_type or "") == lead_type]

    supplier_ids = {s.id for s in suppliers}
    contacts = list(
        db.scalars(
            select(Contact).where(
                Contact.contact_type.in_(["whatsapp", "wechat", "telegram"]),
            )
        ).all()
    )
    # Always apply supplier filter when brand/lead_type was requested (even if empty)
    if brand or lead_type:
        contacts = [c for c in contacts if c.supplier_id in supplier_ids]
    elif supplier_ids:
        contacts = [c for c in contacts if c.supplier_id in supplier_ids]

    supplier_map = {s.id: s for s in suppliers}
    scored = []
    for c in contacts:
        s = supplier_map.get(c.supplier_id) if c.supplier_id else None
        sc = living_score(c, s)
        if sc < min_living:
            continue
        scored.append((c, s, sc))

    evidences = []
    if supplier_ids:
        evidences = list(
            db.scalars(select(Evidence).where(Evidence.supplier_id.in_(supplier_ids)).limit(5000)).all()
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # README
        readme = (
            "WAREACH case pack\n"
            "==================\n"
            f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}\n"
            f"Filter brand: {brand or 'all'}\n"
            f"Filter lead_type: {lead_type or 'all'}\n"
            f"Min living_score: {min_living}\n\n"
            "Contents:\n"
            "- suppliers.csv — suspected sellers / factories\n"
            "- contacts.csv — WhatsApp / WeChat / Telegram with living_score\n"
            "- evidences.csv — captured URLs / excerpts\n"
            "- meta.json — counts\n\n"
            "Use for brand-protection investigation only. Verify contacts manually.\n"
            "Do not mass-message numbers from this file.\n"
        )
        zf.writestr("README.txt", readme)

        # suppliers
        sbuf = io.StringIO()
        sw = csv.writer(sbuf)
        sw.writerow(
            [
                "id",
                "display_name",
                "lead_type",
                "quality_tier",
                "platform",
                "url",
                "brands",
                "geo_clusters",
                "risk_score",
                "priority_score",
                "status",
                "region",
            ]
        )
        for s in suppliers:
            sw.writerow(
                [
                    s.id,
                    s.display_name,
                    s.lead_type,
                    s.quality_tier,
                    s.primary_platform,
                    s.primary_url,
                    "|".join(s.brands or []),
                    "|".join(s.geo_clusters or []),
                    s.risk_score,
                    s.priority_score,
                    s.status,
                    s.region_hint,
                ]
            )
        zf.writestr("suppliers.csv", sbuf.getvalue())

        # contacts
        cbuf = io.StringIO()
        cw = csv.writer(cbuf)
        cw.writerow(
            [
                "contact_id",
                "type",
                "value",
                "living_score",
                "verify_status",
                "wa_me",
                "brand",
                "source_url",
                "supplier_id",
                "supplier_name",
                "lead_type",
                "seen_count",
                "first_seen",
                "last_seen",
            ]
        )
        for c, s, sc in scored:
            digits = "".join(ch for ch in c.normalized_value if ch.isdigit())
            wa = f"https://wa.me/{digits}" if c.contact_type == "whatsapp" and digits else ""
            cw.writerow(
                [
                    c.id,
                    c.contact_type,
                    c.normalized_value,
                    sc,
                    c.verify_status or "unverified",
                    wa,
                    c.brand_context,
                    c.source_url,
                    c.supplier_id,
                    s.display_name if s else "",
                    s.lead_type if s else "",
                    c.seen_count,
                    c.first_seen_at.isoformat() if c.first_seen_at else "",
                    c.last_seen_at.isoformat() if c.last_seen_at else "",
                ]
            )
        zf.writestr("contacts.csv", cbuf.getvalue())

        # evidences
        ebuf = io.StringIO()
        ew = csv.writer(ebuf)
        ew.writerow(["id", "supplier_id", "url", "title", "excerpt", "brands", "captured_at"])
        for e in evidences:
            ew.writerow(
                [
                    e.id,
                    e.supplier_id,
                    e.url,
                    (e.title or "")[:300],
                    (e.excerpt or "")[:500],
                    "|".join(e.brands_detected or []),
                    e.captured_at.isoformat() if e.captured_at else "",
                ]
            )
        zf.writestr("evidences.csv", ebuf.getvalue())

        zf.writestr(
            "meta.json",
            json.dumps(
                {
                    "suppliers": len(suppliers),
                    "contacts": len(scored),
                    "evidences": len(evidences),
                    "brand": brand,
                    "lead_type": lead_type,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
        )

    return buf.getvalue()
