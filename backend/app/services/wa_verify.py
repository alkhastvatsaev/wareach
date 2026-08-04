"""Run Baileys WhatsApp existence checks (avis-google port) against WAREACH contacts."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Contact, JobRun
from app.services.pipeline import utcnow

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]  # wareach/
WA_DIR = ROOT / "tools" / "whatsapp"
PENDING = WA_DIR / "data" / "pending.json"
RESULTS = WA_DIR / "data" / "results.json"

# Map Baileys oui/non → WAREACH verify_status
STATUS_MAP = {
    "oui": "reachable",
    "non": "dead",
    "invalide": "dead",
    "erreur": "unverified",  # retry later
}


def _node_bin() -> str:
    return "node"


def auth_ready() -> bool:
    creds = WA_DIR / "auth" / "creds.json"
    return creds.is_file()


def export_pending(db: Session, *, limit: int = 80) -> list[dict]:
    rows = list(
        db.scalars(
            select(Contact)
            .where(Contact.contact_type == "whatsapp")
            .where(
                or_(
                    Contact.verify_status == "unverified",
                    Contact.verify_status.is_(None),
                    Contact.verify_status == "busy",
                )
            )
            .order_by(Contact.last_seen_at.desc())
            .limit(limit)
        )
    )
    payload = [
        {"id": c.id, "phone": c.normalized_value, "raw": c.raw_value}
        for c in rows
    ]
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    PENDING.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def import_results(db: Session) -> dict:
    if not RESULTS.exists():
        return {"imported": 0, "error": "no_results"}
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {"imported": 0, "error": "bad_results"}

    reachable = dead = skipped = 0
    for item in data:
        cid = item.get("id")
        wa = str(item.get("whatsapp") or "").lower()
        status = STATUS_MAP.get(wa)
        if not cid or not status:
            skipped += 1
            continue
        if status == "unverified":
            skipped += 1
            continue
        row = db.get(Contact, int(cid))
        if not row:
            skipped += 1
            continue
        row.verify_status = status
        note = f"baileys:{wa}"
        if item.get("jid"):
            note += f" jid={item['jid']}"
        row.verify_note = note[:255]
        row.verified_at = utcnow()
        if status == "reachable":
            reachable += 1
        else:
            dead += 1
    db.commit()
    return {
        "imported": reachable + dead,
        "reachable": reachable,
        "dead": dead,
        "skipped": skipped,
    }


def run_whatsapp_verify(
    db: Session,
    *,
    limit: int = 50,
    delay_ms: int = 4000,
    login_only: bool = False,
) -> dict:
    """
    Export pending → Node Baileys check → import results into Contact.verify_status.
    Requires prior QR login (npm run login in tools/whatsapp).
    """
    job = JobRun(job_type="whatsapp_verify", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    if not (WA_DIR / "node_modules").exists():
        stats = {"ok": False, "error": "node_modules missing — run: cd tools/whatsapp && npm install"}
        job.status = "failed"
        job.error = stats["error"]
        job.finished_at = utcnow()
        job.stats = stats
        db.commit()
        return stats

    if not login_only and not auth_ready():
        stats = {
            "ok": False,
            "error": "WhatsApp session manquante — lance ./scripts/whatsapp-login.sh (scan QR)",
            "auth_ready": False,
        }
        job.status = "failed"
        job.error = stats["error"]
        job.finished_at = utcnow()
        job.stats = stats
        db.commit()
        return stats

    pending = [] if login_only else export_pending(db, limit=limit)
    if not login_only and not pending:
        stats = {"ok": True, "pending": 0, "message": "aucun contact unverified"}
        job.status = "done"
        job.finished_at = utcnow()
        job.stats = stats
        db.commit()
        return stats

    cmd = [_node_bin(), str(WA_DIR / "check_batch.js")]
    if login_only:
        cmd.append("--login-only")

    env = {
        **os.environ,
        "DELAY_MS": str(delay_ms),
        "MAX_CHECKS": str(limit),
        "WA_PENDING": str(PENDING),
        "WA_RESULTS": str(RESULTS),
        "WA_AUTH_DIR": str(WA_DIR / "auth"),
    }

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WA_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=60 * 60,  # 1h max batch
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stats = {"ok": False, "error": f"timeout: {exc}"}
        job.status = "failed"
        job.error = stats["error"]
        job.finished_at = utcnow()
        job.stats = stats
        db.commit()
        return stats

    log_tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-2000:]
    if proc.returncode != 0:
        stats = {
            "ok": False,
            "error": f"node exit {proc.returncode}",
            "log_tail": log_tail,
            "pending": len(pending),
        }
        job.status = "failed"
        job.error = stats["error"]
        job.finished_at = utcnow()
        job.stats = stats
        db.commit()
        return stats

    imported = {"imported": 0} if login_only else import_results(db)
    stats = {
        "ok": True,
        "pending": len(pending),
        "auth_ready": auth_ready(),
        "import": imported,
        "log_tail": log_tail[-800:],
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("whatsapp_verify done: %s", {k: stats[k] for k in ("pending", "import", "ok")})
    return stats
