"""Pace / health alerts persisted for ops UI."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import SystemMetric
from app.services.pace import contact_pace


def evaluate_alerts(db: Session) -> dict:
    pace = contact_pace(db)
    alerts: list[dict] = []
    wa = pace["whatsapp"]
    wa_h = pace["wa_per_hour"] or 0
    needed = 1429 / 24  # ~59.5/h for 10k/week

    if wa_h < needed * 0.25:
        alerts.append(
            {
                "level": "critical",
                "code": "pace_too_low",
                "message": f"WA pace {wa_h}/h << needed ~{round(needed)}/h for 10k/week",
            }
        )
    elif wa_h < needed * 0.5:
        alerts.append(
            {
                "level": "warn",
                "code": "pace_behind",
                "message": f"WA pace {wa_h}/h behind target ~{round(needed)}/h",
            }
        )

    if pace.get("eta_hours_to_10k_wa") and pace["eta_hours_to_10k_wa"] > 24 * 10:
        alerts.append(
            {
                "level": "warn",
                "code": "eta_long",
                "message": f"ETA to 10k WA ≈ {pace['eta_hours_to_10k_wa']}h",
            }
        )

    if wa >= 10000:
        alerts.append({"level": "info", "code": "target_hit", "message": "WhatsApp target 10k reached"})

    payload = {
        "alerts": alerts,
        "pace": pace,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    row = db.scalar(select(SystemMetric).where(SystemMetric.key == "alerts"))
    if not row:
        db.add(SystemMetric(key="alerts", value=payload))
    else:
        row.value = payload
        row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return payload
