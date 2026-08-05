"""LuxMatch API — photo RFQ marketplace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services import luxmatch as lm

router = APIRouter(prefix="/luxmatch", tags=["luxmatch"])


class ConfirmIn(BaseModel):
    request_id: int
    user_edit: str | None = None
    contact_email: str | None = None
    contact_telegram: str | None = None
    start_blast: bool = True


class QuoteIn(BaseModel):
    price: float = Field(..., gt=0)
    currency: str = "USD"
    description: str | None = None
    shipping: str | None = None
    payment_methods: list[str] = Field(default_factory=list)


class SelectIn(BaseModel):
    quote_id: int


class ReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


@router.post("/analyze")
async def analyze(file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    if not data or len(data) < 100:
        raise HTTPException(400, "empty image")
    if len(data) > 12_000_000:
        raise HTTPException(400, "image too large (max 12MB)")
    ct = file.content_type or "image/jpeg"
    path, url_path = lm.save_upload(data, filename=file.filename or "photo.jpg")
    desc = lm.analyze_image(data, content_type=ct)
    row = lm.create_draft_request(db, photo_path=path, photo_url=url_path, ai_description=desc)
    return {
        "ok": True,
        "request_id": row.id,
        "client_token": row.client_token,
        "photo_url": row.photo_url,
        "ai_description": row.ai_description,
        "status": row.status,
    }


@router.post("/confirm")
def confirm(body: ConfirmIn, db: Session = Depends(get_db)):
    try:
        row = lm.confirm_and_enqueue_blast(
            db,
            request_id=body.request_id,
            user_edit=body.user_edit,
            contact_email=body.contact_email,
            contact_telegram=body.contact_telegram,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if body.start_blast and row.status == "pending_blast" and not row.blast_error:
        lm.start_blast_async(row.id)
    settings = get_settings()
    return {
        "ok": True,
        "request_id": row.id,
        "client_token": row.client_token,
        "status": row.status,
        "blast_error": row.blast_error,
        "client_url": f"{settings.luxmatch_public_url.rstrip('/')}/r/{row.client_token}",
        "outreach_queued": len(lm.build_wa_payload(db, row.id)) if row.id else 0,
    }


@router.post("/r/{token}/blast")
def force_blast(token: str, db: Session = Depends(get_db)):
    from sqlalchemy import select
    from app.models.entities import RfqRequest

    req = db.scalar(select(RfqRequest).where(RfqRequest.client_token == token))
    if not req:
        raise HTTPException(404, "not found")
    result = lm.run_blast(db, req.id)
    return result


@router.get("/r/{token}")
def get_client(token: str, db: Session = Depends(get_db)):
    view = lm.client_view(db, token)
    if not view:
        raise HTTPException(404, "not found")
    return view


@router.get("/s/{token}")
def get_supplier(token: str, db: Session = Depends(get_db)):
    view = lm.supplier_view(db, token)
    if not view:
        raise HTTPException(404, "not found")
    return view


@router.post("/s/{token}/quote")
def post_quote(token: str, body: QuoteIn, db: Session = Depends(get_db)):
    try:
        q = lm.submit_quote(
            db,
            token,
            price=body.price,
            currency=body.currency,
            description=body.description,
            shipping=body.shipping,
            payment_methods=body.payment_methods,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "quote_id": q.id, "price": q.price, "currency": q.currency}


@router.post("/r/{token}/select")
def post_select(token: str, body: SelectIn, db: Session = Depends(get_db)):
    try:
        req = lm.select_quote(db, token, body.quote_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "status": req.status, "selected_quote_id": req.selected_quote_id}


@router.post("/r/{token}/review")
def post_review(token: str, body: ReviewIn, db: Session = Depends(get_db)):
    try:
        rev = lm.add_review(db, token, rating=body.rating, comment=body.comment)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "review_id": rev.id, "rating": rev.rating}


@router.get("/uploads/{name}")
def get_upload(name: str):
    if "/" in name or ".." in name:
        raise HTTPException(400, "bad name")
    path = Path(get_settings().luxmatch_upload_dir) / name
    if not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)
