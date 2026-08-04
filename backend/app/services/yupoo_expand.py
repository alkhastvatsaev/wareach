"""Expand Yupoo graphs: from any shop page, pull sibling *.x.yupoo.com hosts + embedded WA."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import DiscoveredUrl, JobRun
from app.services.discovery import SearchHit
from app.services.pipeline import merge_supplier_from_extraction, upsert_discovered_urls, utcnow
from app.services.whatsapp_harvest import harvest_hit_snippet, whatsapp_count

logger = logging.getLogger(__name__)

YUPOO_HOST = re.compile(r"https?://([a-zA-Z0-9\-]+)\.x\.yupoo\.com[^\s\"'<>]*", re.I)
MOBILE = re.compile(r"(?:whats?a?pp?)?(?:86)?(1[3-9]\d{9})", re.I)


def _fetch_html(url: str) -> str:
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            r = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
            )
            if r.status_code >= 400:
                return ""
            return r.text[:300_000]
    except Exception as exc:
        logger.debug("yupoo fetch fail %s: %s", url, exc)
        return ""


def expand_from_html(html: str, base_url: str) -> tuple[list[SearchHit], list[str]]:
    hits: list[SearchHit] = []
    phones: list[str] = []
    seen: set[str] = set()
    for m in YUPOO_HOST.finditer(html or ""):
        url = m.group(0).rstrip(").,]'\"")
        host = urlparse(url).netloc.lower()
        if not host or host in seen:
            continue
        seen.add(host)
        root = f"https://{host}/"
        title = host.split(".")[0]
        hits.append(SearchHit(url=root, title=title, snippet=url, source="yupoo_expand"))
        for pm in MOBILE.finditer(host):
            phones.append(pm.group(1))
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html or "", re.I):
        href = m.group(1)
        full = urljoin(base_url, href)
        if "x.yupoo.com" not in full:
            continue
        host = urlparse(full).netloc.lower()
        if host and host not in seen:
            seen.add(host)
            hits.append(SearchHit(url=f"https://{host}/", title=host.split(".")[0], source="yupoo_expand"))
    for pm in MOBILE.finditer(html or ""):
        phones.append(pm.group(1))
    return hits, phones


def run_yupoo_expand(db: Session, *, seed_limit: int = 40, prefer_contact: bool = True) -> dict:
    before = whatsapp_count(db)
    job = JobRun(job_type="yupoo_expand", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    candidates = list(
        db.scalars(
            select(DiscoveredUrl)
            .where(DiscoveredUrl.url.ilike("%yupoo%"))
            .where(DiscoveredUrl.status.in_(["pending", "done", "failed"]))
            .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.id.desc())
            .limit(seed_limit * 3)
        )
    )
    by_host: dict[str, DiscoveredUrl] = {}
    for s in candidates:
        host = (s.domain or urlparse(s.url).netloc or "").lower()
        if host and host not in by_host:
            by_host[host] = s
        if len(by_host) >= seed_limit:
            break
    seeds = list(by_host.values())

    urls_added = 0
    shops_found = 0
    contact_ops = 0
    fetched = 0

    for seed in seeds:
        host = urlparse(seed.url).netloc
        paths = [seed.url]
        if prefer_contact and host:
            paths = [f"https://{host}/", f"https://{host}/contact", f"https://{host}/about", seed.url]

        seen_page: set[str] = set()
        for page_url in paths:
            if page_url in seen_page:
                continue
            seen_page.add(page_url)
            html = _fetch_html(page_url)
            if len(html) < 80:
                continue
            fetched += 1
            hits, phones = expand_from_html(html, page_url)
            shops_found += len(hits)
            urls_added += upsert_discovered_urls(
                db, hits, source_query=f"expand:{page_url}", brand_hint=seed.brand_hint, priority=280
            )
            # queue /contact for new shops
            contact_hits = [
                SearchHit(url=h.url.rstrip("/") + "/contact", title=f"{h.title} contact", source="yupoo_expand")
                for h in hits[:40]
            ]
            if contact_hits:
                urls_added += upsert_discovered_urls(
                    db,
                    contact_hits,
                    source_query=f"expand_contact:{page_url}",
                    brand_hint=seed.brand_hint,
                    priority=290,
                )
            text = f"{seed.title or ''}\n{seed.snippet or ''}\n{page_url}\n{html[:12000]}"
            info = merge_supplier_from_extraction(
                db, url=page_url, title=seed.title, text=text, brand_hint=seed.brand_hint
            )
            contact_ops += int(info.get("contacts") or 0)
            for hit in hits[:40]:
                contact_ops += harvest_hit_snippet(db, hit, seed.brand_hint)
            for mobile in phones[:30]:
                fake = SearchHit(
                    url=page_url,
                    title=f"WhatsApp:+86{mobile}",
                    snippet=f"WhatsApp +86{mobile}",
                    source="yupoo_expand",
                )
                contact_ops += harvest_hit_snippet(db, fake, seed.brand_hint)

    after = whatsapp_count(db)
    stats = {
        "seeds": len(seeds),
        "fetched": fetched,
        "shops_found": shops_found,
        "urls_added": urls_added,
        "contact_ops": contact_ops,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("yupoo_expand done: %s", stats)
    return stats
