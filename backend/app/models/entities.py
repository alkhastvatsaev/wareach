from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="zh", index=True)
    platform_hint: Mapped[str] = mapped_column(String(64), default="web")
    category: Mapped[str] = mapped_column(String(64), default="general", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiscoveredUrl(Base):
    __tablename__ = "discovered_urls"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_url_hash"),
        Index("ix_discovered_status_priority", "status", "priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    source_query: Mapped[str | None] = mapped_column(String(512))
    brand_hint: Mapped[str | None] = mapped_column(String(64), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("ix_supplier_score", "risk_score"),
        Index("ix_supplier_priority", "priority_score"),
        Index("ix_supplier_lead_type", "lead_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    primary_platform: Mapped[str | None] = mapped_column(String(64), index=True)
    primary_url: Mapped[str | None] = mapped_column(Text)
    region_hint: Mapped[str | None] = mapped_column(String(128), default="China")
    brands: Mapped[list] = mapped_column(JSON, default=list)
    groups: Mapped[list] = mapped_column(JSON, default=list)
    lead_type: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    quality_tier: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    geo_clusters: Mapped[list] = mapped_column(JSON, default=list)
    signals: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)

    contacts: Mapped[list[Contact]] = relationship(back_populates="supplier")
    evidences: Mapped[list[Evidence]] = relationship(back_populates="supplier")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("contact_type", "normalized_value", name="uq_contact_norm"),
        Index("ix_contact_type_value", "contact_type", "normalized_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_value: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    brand_context: Mapped[str | None] = mapped_column(String(64))
    # unverified | reachable | dead | busy | skip
    verify_status: Mapped[str] = mapped_column(String(32), default="unverified", index=True)
    verify_note: Mapped[str | None] = mapped_column(String(255))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    seen_count: Mapped[int] = mapped_column(Integer, default=1)

    supplier: Mapped[Supplier | None] = relationship(back_populates="contacts")


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text)
    brands_detected: Mapped[list] = mapped_column(JSON, default=list)
    raw_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    supplier: Mapped[Supplier | None] = relationship(back_populates="evidences")


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsumerLead(Base):
    """Phase 2 — French / EU replica buyers & curators discovered via OSINT."""

    __tablename__ = "consumer_leads"
    __table_args__ = (
        UniqueConstraint("platform", "handle", name="uq_consumer_platform_handle"),
        Index("ix_consumer_buyer_score", "buyer_score"),
        Index("ix_consumer_status", "contact_status"),
        Index("ix_consumer_country", "country_hint"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    profile_url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="unknown", index=True)
    country_hint: Mapped[str | None] = mapped_column(String(8), index=True)
    brands_interest: Mapped[list] = mapped_column(JSON, default=list)
    buyer_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    lead_role: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    # found | queued | contacted | engaged | opted_out
    contact_status: Mapped[str] = mapped_column(String(32), default="found", index=True)
    contact_method: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    supplier_ref: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    seen_count: Mapped[int] = mapped_column(Integer, default=1)


# ─── LuxMatch RFQ marketplace ───────────────────────────────────────


class RfqRequest(Base):
    """Buyer photo request → AI description → blast to suppliers."""

    __tablename__ = "rfq_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    photo_path: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(Text)
    ai_description: Mapped[dict] = mapped_column(JSON, default=dict)
    user_edit: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    # draft | confirmed | pending_blast | blasting | blasted | selected | completed
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_telegram: Mapped[str | None] = mapped_column(String(128))
    selected_quote_id: Mapped[int | None] = mapped_column(Integer)
    blast_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RfqOutreach(Base):
    """One WhatsApp outreach to a supplier for an RFQ."""

    __tablename__ = "rfq_outreach"
    __table_args__ = (UniqueConstraint("supplier_token", name="uq_rfq_supplier_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("rfq_requests.id"), index=True, nullable=False)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), index=True)
    phone: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    supplier_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    wa_status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    # queued | sent | failed
    wa_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RfqQuote(Base):
    __tablename__ = "rfq_quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outreach_id: Mapped[int] = mapped_column(ForeignKey("rfq_outreach.id"), index=True, nullable=False)
    request_id: Mapped[int] = mapped_column(ForeignKey("rfq_requests.id"), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    description: Mapped[str | None] = mapped_column(Text)
    shipping: Mapped[str | None] = mapped_column(Text)
    payment_methods: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="submitted", index=True)
    # submitted | selected | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RfqReview(Base):
    __tablename__ = "rfq_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("rfq_requests.id"), index=True, nullable=False)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), index=True)
    quote_id: Mapped[int | None] = mapped_column(ForeignKey("rfq_quotes.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
