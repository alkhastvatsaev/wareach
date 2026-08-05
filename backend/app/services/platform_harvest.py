"""Multi-platform consumer harvest — YouTube, Telegram, Discord, FR forums.

Uses free scrapers only (SearX / DDG / Jina). No Firecrawl.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.entities import JobRun
from app.services.demand_discovery import detect_brands, score_consumer_text, upsert_consumer_lead
from app.services.free_search import free_web_search, platform_from_url, read_page_free

logger = logging.getLogger(__name__)

# Public Telegram channels often mentioned in FR replica communities
TELEGRAM_CHANNELS = [
    "repsneakers",
    "fashionreps",
    "luxurylife",
    "qcfinds",
    "findseller",
]

YOUTUBE_QUERIES = [
    'site:youtube.com "réplique" OR "replica" france pandabuy',
    'site:youtube.com yupoo "louis vuitton" OR hermès haul français',
    'site:youtube.com "comment commander" pandabuy OR cssbuy france',
    'site:youtube.com "QC" replica bag france OR français',
    'site:youtube.com "guide yupoo" français',
]

DISCORD_QUERIES = [
    'discord.gg replica OR fashionreps OR "QC" france',
    'site:discord.com "pandabuy" OR yupoo france',
    '"discord" "réplique" OR replica "france" seller',
]

FORUM_QUERIES = [
    'site:dealabs.com réplique OR replica OR yupoo OR pandabuy',
    '"yupoo" OR pandabuy site:reddit.com/r/france',
    'réplique sac "où commander" OR "quel vendeur" france',
    '"1:1" OR "mirror quality" telegram france',
]

TG_HANDLE_RE = re.compile(r"(?:t\.me/|@)([A-Za-z0-9_]{4,32})")
YT_HANDLE_RE = re.compile(
    r"(?:youtube\.com/(?:@|channel/|c/|user/)|youtu\.be/)([A-Za-z0-9_\-.]{2,64})"
)
DISCORD_INVITE_RE = re.compile(r"(?:discord\.gg|discord\.com/invite)/([A-Za-z0-9\-]+)")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _handle_from_url(url: str, platform: str, fallback: str = "") -> str:
    if platform == "youtube":
        m = YT_HANDLE_RE.search(url or "")
        if m:
            return m.group(1)[:255]
    if platform == "telegram":
        m = TG_HANDLE_RE.search(url or "")
        if m:
            return m.group(1)[:255]
    if platform == "discord":
        m = DISCORD_INVITE_RE.search(url or "")
        if m:
            return f"invite:{m.group(1)}"[:255]
    return (fallback or hashlib.sha256((url or "x").encode()).hexdigest()[:16])[:255]


def harvest_youtube(db: Session, *, max_queries: int = 5) -> dict:
    """Find FR buyer signals on YouTube via free web search + page read."""
    leads_added = 0
    leads_updated = 0
    hits_seen = 0

    for q in YOUTUBE_QUERIES[:max_queries]:
        for hit in free_web_search(q, max_results=8):
            url = hit.url or ""
            if "youtube.com" not in url and "youtu.be" not in url:
                continue
            hits_seen += 1
            text = f"{hit.title or ''}\n{hit.snippet or ''}"
            # Enrich with page text when title/snippet weak
            if len(text) < 80:
                page = read_page_free(url, max_chars=4000)
                if page:
                    text = f"{text}\n{page[:3000]}"
            score, role, country = score_consumer_text(text)
            if score < 30:
                continue
            handle = _handle_from_url(url, "youtube")
            _, created = upsert_consumer_lead(
                db,
                platform="youtube",
                handle=handle,
                display_name=hit.title[:120] if hit.title else None,
                profile_url=url,
                language="fr" if country == "FR" else "unknown",
                country_hint=country,
                brands_interest=detect_brands(text),
                buyer_score=score,
                lead_role=role,
                source_type="platform_youtube",
                source_url=url,
                snippet=text[:1500],
                meta={"query": q, "engine": hit.source},
            )
            leads_added += int(created)
            leads_updated += int(not created)

    return {"hits": hits_seen, "leads_added": leads_added, "leads_updated": leads_updated}


def harvest_telegram(db: Session, *, max_channels: int = 5, max_search: int = 4) -> dict:
    """Scrape public t.me/s/{channel} pages + search for FR telegram mentions."""
    leads_added = 0
    leads_updated = 0
    pages_read = 0

    # Public channel scrapes
    for ch in TELEGRAM_CHANNELS[:max_channels]:
        url = f"https://t.me/s/{ch}"
        text = read_page_free(url, max_chars=12000)
        if not text or len(text) < 100:
            continue
        pages_read += 1
        # Split into rough post chunks
        chunks = re.split(r"\n{2,}", text)
        for chunk in chunks[:30]:
            if len(chunk) < 40:
                continue
            score, role, country = score_consumer_text(chunk)
            # Boost FR / buyer mentions even without strong FR signal on EN channels
            if score < 25 and not re.search(r"france|français|yupoo|pandabuy|w2c", chunk, re.I):
                continue
            if score < 25:
                score = max(score, 28.0)
            handle = ch
            # Prefer @handles found in chunk
            m = TG_HANDLE_RE.search(chunk)
            if m and m.group(1).lower() != ch.lower():
                handle = m.group(1)
            _, created = upsert_consumer_lead(
                db,
                platform="telegram",
                handle=handle,
                display_name=f"@{handle}",
                profile_url=f"https://t.me/{handle}",
                language="fr" if country == "FR" else "unknown",
                country_hint=country,
                brands_interest=detect_brands(chunk),
                buyer_score=score,
                lead_role=role if role != "unknown" else "curator",
                source_type="platform_telegram",
                source_url=url,
                snippet=chunk[:1500],
                meta={"channel": ch},
            )
            leads_added += int(created)
            leads_updated += int(not created)

    # Web search for FR Telegram communities
    search_qs = [
        't.me réplique OR replica OR yupoo france',
        'telegram "pandabuy" OR "cssbuy" français OR france',
        'site:t.me hermès OR "louis vuitton" replica',
        '"canal telegram" réplique france',
    ]
    for q in search_qs[:max_search]:
        for hit in free_web_search(q, max_results=6):
            url = hit.url or ""
            plat = platform_from_url(url)
            if plat not in {"telegram", "web"}:
                continue
            text = f"{hit.title or ''}\n{hit.snippet or ''}"
            score, role, country = score_consumer_text(text)
            if score < 28:
                continue
            handle = _handle_from_url(url, "telegram", fallback=hashlib.sha256(url.encode()).hexdigest()[:12])
            _, created = upsert_consumer_lead(
                db,
                platform="telegram" if plat == "telegram" else "web",
                handle=handle,
                profile_url=url if plat == "telegram" else f"https://t.me/{handle}" if handle else url,
                language="fr" if country == "FR" else "unknown",
                country_hint=country,
                brands_interest=detect_brands(text),
                buyer_score=score,
                lead_role=role,
                source_type="platform_telegram_web",
                source_url=url,
                snippet=text[:1500],
                meta={"query": q},
            )
            leads_added += int(created)
            leads_updated += int(not created)

    return {"pages_read": pages_read, "leads_added": leads_added, "leads_updated": leads_updated}


def harvest_discord(db: Session, *, max_queries: int = 3) -> dict:
    """Find Discord invites / mentions linked to FR replica buyers."""
    leads_added = 0
    leads_updated = 0
    hits_seen = 0

    for q in DISCORD_QUERIES[:max_queries]:
        for hit in free_web_search(q, max_results=8):
            url = hit.url or ""
            text = f"{hit.title or ''}\n{hit.snippet or ''}"
            hits_seen += 1
            score, role, country = score_consumer_text(text)
            invite = DISCORD_INVITE_RE.search(url) or DISCORD_INVITE_RE.search(text)
            if not invite and score < 35:
                continue
            if score < 25:
                score = 30.0
            handle = f"invite:{invite.group(1)}" if invite else _handle_from_url(url, "discord")
            _, created = upsert_consumer_lead(
                db,
                platform="discord",
                handle=handle,
                display_name=hit.title[:120] if hit.title else handle,
                profile_url=url if "discord" in url else (f"https://discord.gg/{invite.group(1)}" if invite else url),
                language="fr" if country == "FR" else "unknown",
                country_hint=country,
                brands_interest=detect_brands(text),
                buyer_score=score,
                lead_role=role if role != "unknown" else "curator",
                source_type="platform_discord",
                source_url=url,
                snippet=text[:1500],
                meta={"query": q},
            )
            leads_added += int(created)
            leads_updated += int(not created)

    return {"hits": hits_seen, "leads_added": leads_added, "leads_updated": leads_updated}


def harvest_forums(db: Session, *, max_queries: int = 4) -> dict:
    """FR forums / Dealabs / misc web buyer signals."""
    leads_added = 0
    leads_updated = 0
    hits_seen = 0

    for q in FORUM_QUERIES[:max_queries]:
        for hit in free_web_search(q, max_results=6):
            url = hit.url or ""
            if "reddit.com" in url:
                continue
            hits_seen += 1
            text = f"{hit.title or ''}\n{hit.snippet or ''}"
            score, role, country = score_consumer_text(text)
            if score < 32:
                continue
            plat = platform_from_url(url)
            handle = _handle_from_url(url, plat)
            _, created = upsert_consumer_lead(
                db,
                platform=plat if plat != "web" else "web",
                handle=handle,
                profile_url=url,
                language="fr" if country == "FR" else "unknown",
                country_hint=country or ("FR" if "dealabs" in url else None),
                brands_interest=detect_brands(text),
                buyer_score=score,
                lead_role=role,
                source_type="platform_forum",
                source_url=url,
                snippet=text[:1500],
                meta={"query": q},
            )
            leads_added += int(created)
            leads_updated += int(not created)

    return {"hits": hits_seen, "leads_added": leads_added, "leads_updated": leads_updated}


def run_platform_harvest(db: Session) -> dict:
    """Full multi-platform harvest cycle."""
    job = JobRun(job_type="platform_harvest", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    yt = harvest_youtube(db)
    tg = harvest_telegram(db)
    dc = harvest_discord(db)
    fm = harvest_forums(db)

    stats = {
        "youtube": yt,
        "telegram": tg,
        "discord": dc,
        "forums": fm,
        "leads_added": yt["leads_added"] + tg["leads_added"] + dc["leads_added"] + fm["leads_added"],
        "leads_updated": yt["leads_updated"] + tg["leads_updated"] + dc["leads_updated"] + fm["leads_updated"],
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("platform_harvest done: +%s leads", stats["leads_added"])
    return stats
