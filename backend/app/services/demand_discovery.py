"""Phase 2 — find French replica consumers via reverse lookup + free OSINT."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import ConsumerLead, Contact, DiscoveredUrl, JobRun, Supplier
from app.services.free_search import RedditPost, free_web_search, platform_from_url, read_page_free, reddit_search

logger = logging.getLogger(__name__)

BRAND_PATTERNS = {
    "hermes": re.compile(r"hermes|birkin|kelly|爱马仕", re.I),
    "louis_vuitton": re.compile(r"louis\s*vuitton|\blv\b|neverfull|speedy|路易威登", re.I),
    "chanel": re.compile(r"chanel|香奈儿", re.I),
    "cartier": re.compile(r"cartier|卡地亚|love\s*bracelet", re.I),
    "van_cleef_arpels": re.compile(r"van\s*cleef|vca|alhambra|梵克雅宝", re.I),
    "dior": re.compile(r"dior|book\s*tote|迪奥", re.I),
    "gucci": re.compile(r"gucci|古驰", re.I),
}

FR_SIGNALS = re.compile(
    r"france|français|francais|paris|lyon|marseille|belgique|suisse|"
    r"colissimo|chronopost|douane|tva|livraison\s+fr|depuis\s+la\s+france|"
    r"\bfr\b|🇫🇷",
    re.I,
)
BUYER_SIGNALS = re.compile(
    r"\bqc\b|haul|received|arrived|agent|pandabuy|cssbuy|sugargoo|hagobuy|"
    r"w2c|gl\b|rl\b|help\s+me\s+find|which\s+seller|safe\s+to\s+order|"
    r"customs|shipping\s+to|first\s+time\s+buy|beginner|"
    r"commander|acheter|livré|reçu|quel\s+agent|ça\s+est\s+passé",
    re.I,
)
SELLER_SIGNALS = re.compile(
    r"factory|wholesale|catalog|yupoo\.com/albums|wechat\s*:|whatsapp\s*:\+?86|"
    r"contact\s*me|dm\s+for\s+price|seller\s+list|trusted\s+seller\s+list",
    re.I,
)

REPLICA_SUBREDDITS = {
    "fashionreps",
    "repladies",
    "designerreps",
    "repsneakers",
    "qualityreps",
    "couturereps",
    "repladiesdesigner",
    "handbags",
    "luxuryreps",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def detect_brands(text: str) -> list[str]:
    return [b for b, pat in BRAND_PATTERNS.items() if pat.search(text or "")]


def score_consumer_text(text: str, *, subreddit: str = "") -> tuple[float, str, str | None]:
    """Return (buyer_score, lead_role, country_hint)."""
    blob = text or ""
    score = 0.0
    if FR_SIGNALS.search(blob):
        score += 35
    if BUYER_SIGNALS.search(blob):
        score += 30
    if SELLER_SIGNALS.search(blob):
        score -= 25
    if subreddit.lower() in REPLICA_SUBREDDITS:
        score += 20
    if re.search(r"réplique|replique|fake|1:1|replica|copie|dupe", blob, re.I):
        score += 15

    role = "unknown"
    if score >= 45 and not SELLER_SIGNALS.search(blob):
        role = "buyer"
    elif SELLER_SIGNALS.search(blob):
        role = "seller"
    elif score >= 35:
        role = "curator"

    country = "FR" if FR_SIGNALS.search(blob) else None
    return max(0.0, min(100.0, score)), role, country


def upsert_consumer_lead(
    db: Session,
    *,
    platform: str,
    handle: str,
    display_name: str | None = None,
    profile_url: str | None = None,
    language: str = "unknown",
    country_hint: str | None = None,
    brands_interest: list[str] | None = None,
    buyer_score: float = 0.0,
    lead_role: str = "unknown",
    source_type: str = "unknown",
    source_url: str | None = None,
    supplier_id: int | None = None,
    supplier_ref: str | None = None,
    snippet: str | None = None,
    meta: dict | None = None,
) -> tuple[ConsumerLead | None, bool]:
    handle = (handle or "").strip().lstrip("@")[:255]
    if not handle or handle.lower() in {"[deleted]", "automoderator", "unknown"}:
        return None, False

    existing = db.scalar(
        select(ConsumerLead).where(
            ConsumerLead.platform == platform,
            ConsumerLead.handle == handle,
        )
    )
    brands = brands_interest or []
    if existing:
        existing.seen_count = (existing.seen_count or 0) + 1
        existing.last_seen_at = utcnow()
        existing.buyer_score = max(float(existing.buyer_score or 0), float(buyer_score))
        if brands:
            merged = list(dict.fromkeys((existing.brands_interest or []) + brands))
            existing.brands_interest = merged
        if country_hint and not existing.country_hint:
            existing.country_hint = country_hint
        if lead_role != "unknown" and existing.lead_role == "unknown":
            existing.lead_role = lead_role
        if snippet and (not existing.snippet or len(snippet) > len(existing.snippet or "")):
            existing.snippet = snippet[:2000]
        if supplier_id and not existing.supplier_id:
            existing.supplier_id = supplier_id
        if supplier_ref and not existing.supplier_ref:
            existing.supplier_ref = supplier_ref
        if meta:
            existing.meta = {**(existing.meta or {}), **meta}
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        return existing, False

    row = ConsumerLead(
        platform=platform,
        handle=handle,
        display_name=display_name,
        profile_url=profile_url,
        language=language,
        country_hint=country_hint,
        brands_interest=brands,
        buyer_score=buyer_score,
        lead_role=lead_role,
        source_type=source_type,
        source_url=source_url,
        supplier_id=supplier_id,
        supplier_ref=supplier_ref,
        snippet=(snippet or "")[:2000] or None,
        meta=meta or {},
    )
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
        return row, True
    except IntegrityError:
        db.rollback()
        return None, False


def _lead_from_reddit_post(
    post: RedditPost,
    *,
    source_type: str,
    supplier_id: int | None = None,
    supplier_ref: str | None = None,
) -> dict:
    blob = f"{post.title}\n{post.selftext}"
    score, role, country = score_consumer_text(blob, subreddit=post.subreddit)
    lang = "fr" if country == "FR" else ("en" if post.subreddit.lower() in REPLICA_SUBREDDITS else "unknown")
    return {
        "platform": "reddit",
        "handle": post.author,
        "display_name": post.author,
        "profile_url": f"https://www.reddit.com/user/{post.author}",
        "language": lang,
        "country_hint": country,
        "brands_interest": detect_brands(blob),
        "buyer_score": score,
        "lead_role": role,
        "source_type": source_type,
        "source_url": post.permalink,
        "supplier_id": supplier_id,
        "supplier_ref": supplier_ref,
        "snippet": blob[:1500],
        "meta": {
            "subreddit": post.subreddit,
            "score": post.score,
            "num_comments": post.num_comments,
            "post_url": post.url,
        },
    }


def _supplier_search_terms(db: Session, supplier: Supplier, contacts: list[Contact]) -> list[str]:
    terms: list[str] = []
    url = supplier.primary_url or ""
    if "yupoo" in url.lower():
        host = re.sub(r"^https?://", "", url).split("/")[0]
        sub = host.split(".")[0] if host else ""
        if sub and len(sub) > 2:
            terms.append(sub)
            terms.append(host)
    for c in contacts:
        if c.contact_type == "whatsapp":
            digits = re.sub(r"\D", "", c.normalized_value or "")
            if len(digits) >= 11:
                terms.append(digits[-11:])
    key = supplier.canonical_key or ""
    if key and len(key) > 4:
        terms.append(key)
    return list(dict.fromkeys(t for t in terms if t))


def reverse_lookup_suppliers(
    db: Session,
    *,
    limit: int = 40,
    reddit_limit: int = 15,
) -> dict:
    """For each known supplier — find Reddit/web posts linking to them → consumer leads."""
    job = JobRun(job_type="reverse_lookup", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    suppliers = list(
        db.scalars(
            select(Supplier)
            .where(
                or_(
                    Supplier.primary_url.ilike("%yupoo%"),
                    Supplier.primary_platform.in_(["yupoo", "weidian", "whatsapp"]),
                )
            )
            .order_by(Supplier.last_seen_at.desc())
            .limit(limit)
        )
    )

    leads_added = 0
    leads_updated = 0
    queries_run = 0
    posts_seen = 0
    web_hits = 0

    for sup in suppliers:
        contacts = list(db.scalars(select(Contact).where(Contact.supplier_id == sup.id).limit(5)))
        terms = _supplier_search_terms(db, sup, contacts)
        if not terms:
            continue
        term = terms[0]

        reddit_queries = [
            f'site:reddit.com "{term}"',
            f'"{term}" pandabuy OR cssbuy',
            f'"{term}" replica',
        ]
        for rq in reddit_queries[:2]:
            queries_run += 1
            for post in reddit_search(rq.replace("site:reddit.com ", ""), limit=reddit_limit):
                posts_seen += 1
                payload = _lead_from_reddit_post(
                    post,
                    source_type="reverse_lookup",
                    supplier_id=sup.id,
                    supplier_ref=term,
                )
                if payload["buyer_score"] < 25 and payload["lead_role"] != "buyer":
                    continue
                row, created = upsert_consumer_lead(db, **payload)
                if row:
                    leads_added += int(created)
                    leads_updated += int(not created)

        web_q = f'"{term}" yupoo france OR replica OR pandabuy'
        for hit in free_web_search(web_q, max_results=8):
            web_hits += 1
            plat = platform_from_url(hit.url or "")
            if plat == "reddit" and hit.url:
                # Parse reddit thread — extract via pullpush url search
                m = re.search(r"reddit\.com/r/(\w+)/comments/(\w+)", hit.url or "")
                if m:
                    sub, pid = m.group(1), m.group(2)
                    for post in reddit_search(f"{sub} {pid}", limit=5):
                        payload = _lead_from_reddit_post(
                            post,
                            source_type="reverse_lookup_web",
                            supplier_id=sup.id,
                            supplier_ref=term,
                        )
                        if payload["buyer_score"] >= 20:
                            _, created = upsert_consumer_lead(db, **payload)
                            leads_added += int(created)
                            leads_updated += int(not created)
                continue
            text = f"{hit.title or ''}\n{hit.snippet or ''}"
            score, role, country = score_consumer_text(text)
            if score < 30:
                continue
            handle = hashlib.sha256((hit.url or term).encode()).hexdigest()[:16]
            _, created = upsert_consumer_lead(
                db,
                platform=plat,
                handle=handle,
                profile_url=hit.url,
                country_hint=country,
                brands_interest=detect_brands(text),
                buyer_score=score,
                lead_role=role,
                source_type="reverse_lookup_web",
                source_url=hit.url,
                supplier_id=sup.id,
                supplier_ref=term,
                snippet=text[:1500],
            )
            leads_added += int(created)
            leads_updated += int(not created)

    stats = {
        "suppliers_scanned": len(suppliers),
        "queries_run": queries_run,
        "reddit_posts_seen": posts_seen,
        "web_hits": web_hits,
        "leads_added": leads_added,
        "leads_updated": leads_updated,
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("reverse_lookup done: %s", stats)
    return stats


def run_fr_consumer_discovery(db: Session, *, query_limit: int = 25) -> dict:
    """Harvest FR-language buyer signals from rep communities (free scrapers only)."""
    from app.seeds.seed_demand_fr import fr_consumer_queries

    job = JobRun(job_type="fr_consumer_discovery", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    queries = fr_consumer_queries()[:query_limit]
    leads_added = 0
    leads_updated = 0
    reddit_posts = 0
    web_hits = 0

    for item in queries:
        q = item["query"]
        brand = item.get("brand", "multi")

        for post in reddit_search(q, limit=20):
            reddit_posts += 1
            blob = f"{post.title}\n{post.selftext}"
            score, role, country = score_consumer_text(blob, subreddit=post.subreddit)
            if score < 30 and role not in {"buyer", "curator"}:
                continue
            _, created = upsert_consumer_lead(
                db,
                platform="reddit",
                handle=post.author,
                display_name=post.author,
                profile_url=f"https://www.reddit.com/user/{post.author}",
                language="fr" if country == "FR" else "en",
                country_hint=country,
                brands_interest=detect_brands(blob) or ([brand] if brand != "multi" else []),
                buyer_score=score,
                lead_role=role,
                source_type="fr_discovery",
                source_url=post.permalink,
                snippet=blob[:1500],
                meta={"subreddit": post.subreddit, "query": q},
            )
            leads_added += int(created)
            leads_updated += int(not created)

        if "site:reddit" not in q.lower():
            for hit in free_web_search(q, max_results=6):
                web_hits += 1
                text = f"{hit.title or ''}\n{hit.snippet or ''}"
                if hit.url and "reddit.com" in hit.url:
                    continue
                score, role, country = score_consumer_text(text)
                if score < 35:
                    continue
                handle = hashlib.sha256((hit.url or q).encode()).hexdigest()[:16]
                _, created = upsert_consumer_lead(
                    db,
                    platform=platform_from_url(hit.url or ""),
                    handle=handle,
                    profile_url=hit.url,
                    language="fr" if country == "FR" else "unknown",
                    country_hint=country,
                    brands_interest=detect_brands(text),
                    buyer_score=score,
                    lead_role=role,
                    source_type="fr_web",
                    source_url=hit.url,
                    snippet=text[:1500],
                    meta={"query": q},
                )
                leads_added += int(created)
                leads_updated += int(not created)

    stats = {
        "queries": len(queries),
        "reddit_posts": reddit_posts,
        "web_hits": web_hits,
        "leads_added": leads_added,
        "leads_updated": leads_updated,
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("fr_consumer_discovery done: %s", stats)
    return stats


def run_demand_cycle(
    db: Session,
    *,
    supplier_limit: int = 30,
    query_limit: int = 20,
    enrich_limit: int = 20,
    include_platforms: bool = True,
    include_enrich: bool = True,
) -> dict:
    """Full Phase 2 cycle: reverse lookup + FR discovery + platforms + enrich."""
    from app.services.consumer_enrich import enrich_pending
    from app.services.platform_harvest import run_platform_harvest

    before = db.scalar(select(func.count()).select_from(ConsumerLead)) or 0
    rev = reverse_lookup_suppliers(db, limit=supplier_limit)
    fr = run_fr_consumer_discovery(db, query_limit=query_limit)
    platforms = run_platform_harvest(db) if include_platforms else {}
    enrich = enrich_pending(db, limit=enrich_limit) if include_enrich else {}
    after = db.scalar(select(func.count()).select_from(ConsumerLead)) or 0
    fr_leads = db.scalar(
        select(func.count()).select_from(ConsumerLead).where(ConsumerLead.country_hint == "FR")
    ) or 0
    buyers = db.scalar(
        select(func.count())
        .select_from(ConsumerLead)
        .where(ConsumerLead.lead_role == "buyer")
        .where(ConsumerLead.buyer_score >= 45)
    ) or 0
    return {
        "consumers_before": before,
        "consumers_after": after,
        "consumers_gained": max(0, after - before),
        "fr_leads": fr_leads,
        "qualified_buyers": buyers,
        "reverse_lookup": rev,
        "fr_discovery": fr,
        "platform_harvest": platforms,
        "enrich": enrich,
    }


def demand_stats(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(ConsumerLead)) or 0
    fr = db.scalar(
        select(func.count()).select_from(ConsumerLead).where(ConsumerLead.country_hint == "FR")
    ) or 0
    buyers = db.scalar(
        select(func.count())
        .select_from(ConsumerLead)
        .where(ConsumerLead.lead_role == "buyer")
        .where(ConsumerLead.buyer_score >= 45)
    ) or 0
    by_platform = dict(
        db.execute(
            select(ConsumerLead.platform, func.count())
            .group_by(ConsumerLead.platform)
            .order_by(func.count().desc())
        ).all()
    )
    by_status = dict(
        db.execute(
            select(ConsumerLead.contact_status, func.count()).group_by(ConsumerLead.contact_status)
        ).all()
    )
    return {
        "consumer_leads": total,
        "fr_leads": fr,
        "qualified_buyers": buyers,
        "by_platform": by_platform,
        "by_status": by_status,
        "contact_found": by_status.get("found", 0),
        "contact_queued": by_status.get("queued", 0),
        "contact_contacted": by_status.get("contacted", 0),
        "contact_engaged": by_status.get("engaged", 0),
    }
