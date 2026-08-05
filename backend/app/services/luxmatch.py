"""LuxMatch — photo RFQ → AI describe → WhatsApp blast → quotes."""

from __future__ import annotations

import base64
import json
import logging
import secrets
import subprocess
import threading
import uuid
from pathlib import Path

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Contact, RfqOutreach, RfqQuote, RfqRequest, RfqReview
from app.services.pipeline import utcnow

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
WA_DIR = ROOT / "tools" / "whatsapp"


def _token(n: int = 24) -> str:
    return secrets.token_urlsafe(n)[:n]


def upload_dir() -> Path:
    settings = get_settings()
    p = Path(settings.luxmatch_upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_upload(data: bytes, *, filename: str = "photo.jpg") -> tuple[str, str]:
    """Return (relative_path, public_url_path)."""
    ext = Path(filename).suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = upload_dir() / name
    path.write_bytes(data)
    rel = str(path)
    url_path = f"/api/luxmatch/uploads/{name}"
    return rel, url_path


def analyze_image(image_bytes: bytes, *, content_type: str = "image/jpeg") -> dict:
    """GPT-4o vision → structured FR product description. Fallback if no key."""
    settings = get_settings()
    key = (settings.openai_api_key or "").strip()
    if not key:
        return {
            "brand": "inconnue",
            "model": "article luxe",
            "category": "sac / accessoire",
            "color": "non déterminée",
            "material": "non déterminée",
            "summary": (
                "Description approximative (IA non configurée — ajoute OPENAI_API_KEY). "
                "Article de luxe visible sur la photo ; précisez marque et modèle avant confirmation."
            ),
            "confidence": 0.2,
            "mock": True,
        }

    b64 = base64.b64encode(image_bytes).decode("ascii")
    mime = content_type if content_type.startswith("image/") else "image/jpeg"
    prompt = (
        "Tu analyses une photo produit (mode / luxe). "
        "Réponds UNIQUEMENT en JSON valide avec les clés: "
        "brand, model, category, color, material, summary (2-3 phrases FR précises), confidence (0-1). "
        "Si incertain, brand='inconnue' et explique dans summary."
    )
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 500,
                },
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return {
                "brand": str(data.get("brand") or "inconnue"),
                "model": str(data.get("model") or ""),
                "category": str(data.get("category") or ""),
                "color": str(data.get("color") or ""),
                "material": str(data.get("material") or ""),
                "summary": str(data.get("summary") or ""),
                "confidence": float(data.get("confidence") or 0.5),
                "mock": False,
            }
    except Exception as exc:
        logger.exception("GPT vision failed")
        return {
            "brand": "inconnue",
            "model": "",
            "category": "",
            "color": "",
            "material": "",
            "summary": f"Analyse IA indisponible ({exc}). Décrivez le produit manuellement.",
            "confidence": 0.0,
            "mock": True,
            "error": str(exc)[:200],
        }


def create_draft_request(
    db: Session,
    *,
    photo_path: str,
    photo_url: str,
    ai_description: dict,
) -> RfqRequest:
    row = RfqRequest(
        client_token=_token(28),
        photo_path=photo_path,
        photo_url=photo_url,
        ai_description=ai_description or {},
        status="draft",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def pick_supplier_phones(db: Session, *, limit: int = 10) -> list[Contact]:
    """Prefer reachable WhatsApp, unique normalized phones."""
    reachable = list(
        db.scalars(
            select(Contact)
            .where(Contact.contact_type == "whatsapp")
            .where(Contact.verify_status == "reachable")
            .order_by(Contact.last_seen_at.desc())
            .limit(limit * 4)
        )
    )
    others = list(
        db.scalars(
            select(Contact)
            .where(Contact.contact_type == "whatsapp")
            .where(
                or_(
                    Contact.verify_status == "unverified",
                    Contact.verify_status.is_(None),
                )
            )
            .order_by(Contact.last_seen_at.desc())
            .limit(limit * 4)
        )
    )
    seen: set[str] = set()
    out: list[Contact] = []
    for c in reachable + others:
        digits = "".join(ch for ch in (c.normalized_value or "") if ch.isdigit())
        if len(digits) < 10 or digits in seen:
            continue
        seen.add(digits)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def confirm_and_enqueue_blast(
    db: Session,
    *,
    request_id: int,
    user_edit: str | None = None,
    contact_email: str | None = None,
    contact_telegram: str | None = None,
) -> RfqRequest:
    settings = get_settings()
    row = db.get(RfqRequest, request_id)
    if not row:
        raise ValueError("request not found")
    if user_edit is not None:
        row.user_edit = user_edit.strip()[:4000]
    if contact_email:
        row.contact_email = contact_email.strip()[:255]
    if contact_telegram:
        row.contact_telegram = contact_telegram.strip().lstrip("@")[:128]

    # Clear previous outreach if re-confirm
    old = list(db.scalars(select(RfqOutreach).where(RfqOutreach.request_id == row.id)))
    for o in old:
        db.delete(o)

    contacts = pick_supplier_phones(db, limit=int(settings.luxmatch_blast_limit or 10))
    if not contacts:
        row.status = "pending_blast"
        row.blast_error = "no_whatsapp_contacts"
        row.updated_at = utcnow()
        db.commit()
        db.refresh(row)
        return row

    for c in contacts:
        db.add(
            RfqOutreach(
                request_id=row.id,
                contact_id=c.id,
                phone=c.normalized_value or "",
                supplier_token=_token(28),
                wa_status="queued",
            )
        )
    row.status = "pending_blast"
    row.blast_error = None
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def _product_line(req: RfqRequest) -> str:
    if req.user_edit and req.user_edit.strip():
        return req.user_edit.strip()[:180]
    ai = req.ai_description or {}
    parts = [ai.get("brand"), ai.get("model"), ai.get("color")]
    line = " ".join(str(p) for p in parts if p and str(p) != "inconnue")
    if not line:
        line = str(ai.get("summary") or "article demandé")[:180]
    return line


def build_wa_payload(db: Session, request_id: int) -> list[dict]:
    settings = get_settings()
    base = settings.luxmatch_public_url.rstrip("/")
    req = db.get(RfqRequest, request_id)
    if not req:
        return []
    line = _product_line(req)
    rows = list(db.scalars(select(RfqOutreach).where(RfqOutreach.request_id == request_id)))
    payload = []
    for o in rows:
        link = f"{base}/s/{o.supplier_token}"
        msg = (
            f"LuxMatch — demande client\n"
            f"Produit: {line}\n"
            f"Merci de remplir votre devis (prix, shipping, paiement) ici:\n{link}\n"
            f"Lien valable 48h."
        )
        payload.append(
            {
                "outreach_id": o.id,
                "phone": o.phone,
                "message": msg,
            }
        )
    return payload


def run_blast(db: Session, request_id: int) -> dict:
    """Write pending_rfq.json and run send-rfq.js; update outreach statuses."""
    req = db.get(RfqRequest, request_id)
    if not req:
        return {"ok": False, "error": "not_found"}
    req.status = "blasting"
    req.updated_at = utcnow()
    db.commit()

    payload = build_wa_payload(db, request_id)
    pending_path = WA_DIR / "data" / "pending_rfq.json"
    results_path = WA_DIR / "data" / "rfq_results.json"
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if results_path.exists():
        results_path.unlink()

    creds = WA_DIR / "auth" / "creds.json"
    if not creds.is_file():
        req.status = "pending_blast"
        req.blast_error = "whatsapp_auth_missing — run: cd tools/whatsapp && npm run login"
        req.updated_at = utcnow()
        db.commit()
        return {"ok": False, "error": req.blast_error, "queued": len(payload)}

    script = WA_DIR / "send-rfq.js"
    proc_err = ""
    try:
        proc = subprocess.run(
            ["node", str(script)],
            cwd=str(WA_DIR),
            capture_output=True,
            text=True,
            timeout=600,
            env={
                **dict(__import__("os").environ),
                "WA_RFQ_PENDING": str(pending_path),
                "WA_RFQ_RESULTS": str(results_path),
                "DELAY_MS": "10000",
            },
        )
        logger.info("send-rfq exit=%s stdout=%s", proc.returncode, (proc.stdout or "")[-500:])
        if proc.returncode != 0:
            proc_err = (proc.stderr or proc.stdout or "send_failed")[:500]
            req.blast_error = proc_err
    except Exception as exc:
        logger.exception("blast failed")
        req.status = "pending_blast"
        req.blast_error = str(exc)[:400]
        req.updated_at = utcnow()
        db.commit()
        return {"ok": False, "error": str(exc)}

    sent = failed = 0
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
        except Exception:
            results = []
        by_id = {int(r["outreach_id"]): r for r in results if r.get("outreach_id") is not None}
        for o in db.scalars(select(RfqOutreach).where(RfqOutreach.request_id == request_id)):
            r = by_id.get(o.id)
            if not r:
                continue
            if r.get("ok"):
                o.wa_status = "sent"
                o.sent_at = utcnow()
                o.wa_error = None
                sent += 1
            else:
                o.wa_status = "failed"
                o.wa_error = str(r.get("error") or "failed")[:300]
                failed += 1
    else:
        # Script crashed before writing results (e.g. WA 401 logged out)
        err = proc_err or "whatsapp_send_failed — npm run login in tools/whatsapp"
        for o in db.scalars(select(RfqOutreach).where(RfqOutreach.request_id == request_id)):
            if o.wa_status == "queued":
                o.wa_status = "failed"
                o.wa_error = err[:300]
                failed += 1
        req.blast_error = err
        req.status = "pending_blast"
        req.updated_at = utcnow()
        db.commit()
        return {"ok": False, "error": err, "sent": 0, "failed": failed, "total": len(payload)}

    req.status = "blasted"
    req.updated_at = utcnow()
    if failed and not sent:
        req.blast_error = req.blast_error or "all_sends_failed"
    db.commit()
    return {"ok": True, "sent": sent, "failed": failed, "total": len(payload)}


def start_blast_async(request_id: int) -> None:
    def _run() -> None:
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            run_blast(db, request_id)
        finally:
            db.close()

    threading.Thread(target=_run, name=f"luxmatch-blast-{request_id}", daemon=True).start()


def client_view(db: Session, token: str) -> dict | None:
    req = db.scalar(select(RfqRequest).where(RfqRequest.client_token == token))
    if not req:
        return None
    outreaches = list(db.scalars(select(RfqOutreach).where(RfqOutreach.request_id == req.id)))
    quotes = list(
        db.scalars(select(RfqQuote).where(RfqQuote.request_id == req.id).order_by(RfqQuote.price.asc()))
    )
    return {
        "id": req.id,
        "status": req.status,
        "photo_url": req.photo_url,
        "ai_description": req.ai_description,
        "user_edit": req.user_edit,
        "blast_error": req.blast_error,
        "selected_quote_id": req.selected_quote_id,
        "outreach": [
            {"id": o.id, "wa_status": o.wa_status, "phone_masked": _mask(o.phone)} for o in outreaches
        ],
        "quotes": [
            {
                "id": q.id,
                "price": q.price,
                "currency": q.currency,
                "description": q.description,
                "shipping": q.shipping,
                "payment_methods": q.payment_methods,
                "status": q.status,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
            for q in quotes
        ],
        "sent_count": sum(1 for o in outreaches if o.wa_status == "sent"),
        "quote_count": len(quotes),
    }


def _mask(phone: str) -> str:
    d = "".join(c for c in phone if c.isdigit())
    if len(d) < 6:
        return "***"
    return f"+{d[:2]}…{d[-4:]}"


def supplier_view(db: Session, token: str) -> dict | None:
    o = db.scalar(select(RfqOutreach).where(RfqOutreach.supplier_token == token))
    if not o:
        return None
    req = db.get(RfqRequest, o.request_id)
    if not req:
        return None
    existing = db.scalar(select(RfqQuote).where(RfqQuote.outreach_id == o.id))
    return {
        "outreach_id": o.id,
        "request_id": req.id,
        "product": _product_line(req),
        "ai_description": req.ai_description,
        "photo_url": req.photo_url,
        "already_quoted": bool(existing),
        "quote": (
            {
                "price": existing.price,
                "currency": existing.currency,
                "description": existing.description,
                "shipping": existing.shipping,
                "payment_methods": existing.payment_methods,
            }
            if existing
            else None
        ),
    }


def submit_quote(
    db: Session,
    token: str,
    *,
    price: float,
    currency: str = "USD",
    description: str | None = None,
    shipping: str | None = None,
    payment_methods: list[str] | None = None,
) -> RfqQuote:
    o = db.scalar(select(RfqOutreach).where(RfqOutreach.supplier_token == token))
    if not o:
        raise ValueError("invalid token")
    existing = db.scalar(select(RfqQuote).where(RfqQuote.outreach_id == o.id))
    if existing:
        existing.price = float(price)
        existing.currency = (currency or "USD")[:8]
        existing.description = (description or "")[:4000] or None
        existing.shipping = (shipping or "")[:2000] or None
        existing.payment_methods = payment_methods or []
        db.commit()
        db.refresh(existing)
        return existing
    q = RfqQuote(
        outreach_id=o.id,
        request_id=o.request_id,
        price=float(price),
        currency=(currency or "USD")[:8],
        description=(description or "")[:4000] or None,
        shipping=(shipping or "")[:2000] or None,
        payment_methods=payment_methods or [],
        status="submitted",
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def select_quote(db: Session, client_token: str, quote_id: int) -> RfqRequest:
    req = db.scalar(select(RfqRequest).where(RfqRequest.client_token == client_token))
    if not req:
        raise ValueError("invalid client token")
    q = db.get(RfqQuote, quote_id)
    if not q or q.request_id != req.id:
        raise ValueError("invalid quote")
    for other in db.scalars(select(RfqQuote).where(RfqQuote.request_id == req.id)):
        other.status = "selected" if other.id == quote_id else "rejected"
    req.selected_quote_id = quote_id
    req.status = "selected"
    req.updated_at = utcnow()
    db.commit()
    db.refresh(req)
    return req


def add_review(
    db: Session,
    client_token: str,
    *,
    rating: int,
    comment: str | None = None,
) -> RfqReview:
    req = db.scalar(select(RfqRequest).where(RfqRequest.client_token == client_token))
    if not req:
        raise ValueError("invalid client token")
    if not req.selected_quote_id:
        raise ValueError("no selected quote")
    q = db.get(RfqQuote, req.selected_quote_id)
    if not q:
        raise ValueError("quote missing")
    o = db.get(RfqOutreach, q.outreach_id)
    rating = max(1, min(5, int(rating)))
    rev = RfqReview(
        request_id=req.id,
        contact_id=o.contact_id if o else None,
        quote_id=q.id,
        rating=rating,
        comment=(comment or "")[:2000] or None,
    )
    db.add(rev)
    req.status = "completed"
    req.updated_at = utcnow()
    db.commit()
    db.refresh(rev)
    return rev
