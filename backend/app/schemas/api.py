from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_key: str
    display_name: str | None
    primary_platform: str | None
    primary_url: str | None
    region_hint: str | None
    brands: list[Any] = Field(default_factory=list)
    groups: list[Any] = Field(default_factory=list)
    lead_type: str = "unknown"
    quality_tier: str = "unknown"
    geo_clusters: list[Any] = Field(default_factory=list)
    signals: list[Any] = Field(default_factory=list)
    risk_score: float
    priority_score: float = 0
    confidence: float
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    evidence_count: int


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int | None
    contact_type: str
    raw_value: str
    normalized_value: str
    source_url: str | None
    brand_context: str | None
    seen_count: int
    verify_status: str = "unverified"
    verify_note: str | None = None
    verified_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    open_url: str | None = None


class StatsOut(BaseModel):
    suppliers: int
    contacts: int
    whatsapp: int
    wechat: int
    urls_pending: int
    urls_done: int
    urls_total: int
    queries: int
    evidences: int
    hq_replica: int = 0
    jewelry_factory: int = 0
    gray_jeweler: int = 0
    god_tier: int = 0
    high_tier: int = 0
    target_suppliers: int = 10000
    whatsapp_target: int = 10000
    whatsapp_remaining: int = 10000
    daily_pace_needed: int = 1429
    wa_per_hour: float = 0
    contacts_per_hour: float = 0
    eta_hours_to_10k_wa: float | None = None
    wa_new_24h: int = 0
    wx_new_24h: int = 0
    alert_count: int = 0
    top_alert: str | None = None
    engines_cooling: dict[str, float] = {}
    unverified: int = 0
    reachable: int = 0
    dead: int = 0


class JobTriggerOut(BaseModel):
    ok: bool
    job: str
    result: dict[str, Any] | None = None
    task_id: str | None = None


class HealthOut(BaseModel):
    status: str
    agent_reach: dict[str, Any]
    backends: dict[str, bool]
    database: bool
    redis: bool


class ConsumerLeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    handle: str
    display_name: str | None
    profile_url: str | None
    language: str
    country_hint: str | None
    brands_interest: list[Any] = Field(default_factory=list)
    buyer_score: float
    lead_role: str
    contact_status: str
    contact_method: str | None
    source_type: str
    source_url: str | None
    supplier_id: int | None
    supplier_ref: str | None
    snippet: str | None
    first_seen_at: datetime
    last_seen_at: datetime
    seen_count: int


class DemandStatsOut(BaseModel):
    consumer_leads: int
    fr_leads: int
    qualified_buyers: int
    by_platform: dict[str, int] = Field(default_factory=dict)
    contact_found: int = 0
