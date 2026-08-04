"""Probe Yupoo hosts from known WhatsApp numbers — search-engine-free boost path.

When Bing/Baidu/Exa are captcha/429-blocked, this recovers the peak-hour pattern:
Chinese mobiles often appear as `{mobile}.x.yupoo.com` shop subdomains.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Contact, DiscoveredUrl, JobRun
from app.services.discovery import SearchHit
from app.services.pipeline import merge_supplier_from_extraction, upsert_discovered_urls, utcnow
from app.services.whatsapp_harvest import harvest_hit_snippet, whatsapp_count

logger = logging.getLogger(__name__)


def _cn_mobile(value: str | None) -> str | None:
    d = re.sub(r"\D", "", value or "")
    if d.startswith("86") and len(d) >= 13:
        d = d[2:]
    if len(d) == 11 and d.startswith("1"):
        return d
    return None


def _probe_host(host: str) -> tuple[str, bool]:
    url = f"https://{host}/"
    try:
        with httpx.Client(timeout=8, follow_redirects=True) as client:
            r = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            ok = r.status_code < 400 and len(r.text) > 200 and "yupoo" in (r.text[:2000].lower() + host)
            return host, ok
    except Exception:
        return host, False


def _candidate_hosts(mobiles: list[str], known_phone_hosts: list[str], *, mutate: bool) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(host: str):
        h = host.lower()
        if h in seen:
            return
        seen.add(h)
        out.append(h)

    for m in mobiles:
        add(f"{m}.x.yupoo.com")
        add(f"86{m}.x.yupoo.com")
        add(f"whatsapp{m}.x.yupoo.com")
        add(f"wa{m}.x.yupoo.com")

    if mutate:
        for host in known_phone_hosts:
            sub = host.split(".")[0]
            m = re.search(r"(1[3-9]\d{9})", sub)
            if not m:
                continue
            base = m.group(1)
            # mutate last digit + last-2 neighborhood (cheap virgin inventory)
            for d in range(10):
                add(f"{base[:-1]}{d}.x.yupoo.com")
            prefix = base[:-2]
            last2 = int(base[-2:])
            for delta in range(-15, 16):
                n = last2 + delta
                if 0 <= n <= 99:
                    add(f"{prefix}{n:02d}.x.yupoo.com")

    return out


def run_yupoo_phone_probe(
    db: Session,
    *,
    limit: int = 250,
    workers: int = 12,
    mutate: bool = True,
    harvest: bool = True,
) -> dict:
    before = whatsapp_count(db)
    job = JobRun(job_type="yupoo_phone_probe", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    # Mobiles already known as contacts
    contact_vals = list(
        db.scalars(
            select(Contact.normalized_value).where(Contact.contact_type == "whatsapp").limit(5000)
        )
    )
    mobiles = []
    seen_m: set[str] = set()
    for v in contact_vals:
        m = _cn_mobile(v)
        if m and m not in seen_m:
            seen_m.add(m)
            mobiles.append(m)

    # Phone-encoded domains already in inventory
    domains = list(
        db.scalars(
            select(DiscoveredUrl.domain)
            .where(DiscoveredUrl.domain.ilike("%.x.yupoo.com"))
            .distinct()
            .limit(3000)
        )
    )
    known_phone = []
    known_set = { (d or "").lower() for d in domains }
    for d in domains:
        sub = (d or "").split(".")[0]
        if re.search(r"1[3-9]\d{9}", sub or ""):
            known_phone.append(d)

    candidates = _candidate_hosts(mobiles, known_phone, mutate=mutate)
    # Prefer unknown hosts
    candidates = [h for h in candidates if h not in known_set][:limit]

    live: list[str] = []
    probed = 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 16))) as pool:
        futs = {pool.submit(_probe_host, h): h for h in candidates}
        for fut in as_completed(futs):
            probed += 1
            host, ok = fut.result()
            if ok:
                live.append(host)

    hits = []
    for h in live:
        mobile_m = re.search(r"(1[3-9]\d{9})", h)
        snip = f"WhatsApp:+86{mobile_m.group(1)}" if mobile_m else h
        hits.append(
            SearchHit(
                url=f"https://{h}/",
                title=h.split(".")[0],
                snippet=snip,
                source="yupoo_phone_probe",
            )
        )
    # Also queue /contact
    contact_hits = [
        SearchHit(url=f"https://{h}/contact", title=f"{h.split('.')[0]} contact", source="yupoo_phone_probe")
        for h in live
    ]

    urls_added = upsert_discovered_urls(db, hits + contact_hits, "yupoo_phone_probe", None, priority=300)
    contact_ops = 0
    if harvest:
        for host in live:
            root = f"https://{host}"
            mobile_m = re.search(r"(1[3-9]\d{9})", host)
            seed_title = f"WhatsApp:+86{mobile_m.group(1)}" if mobile_m else host
            for path in ("/", "/contact"):
                page_url = root + path
                try:
                    with httpx.Client(timeout=12, follow_redirects=True) as client:
                        r = client.get(
                            page_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                                "Accept-Language": "zh-CN,zh;q=0.9",
                            },
                        )
                        if r.status_code >= 400 or len(r.text) < 80:
                            continue
                        text = f"{seed_title}\n{page_url}\n{r.text[:18000]}"
                        info = merge_supplier_from_extraction(
                            db, url=page_url, title=seed_title, text=text, brand_hint=None
                        )
                        contact_ops += int(info.get("contacts") or 0)
                        contact_ops += harvest_hit_snippet(
                            db,
                            SearchHit(url=page_url, title=seed_title, snippet=seed_title, source="yupoo_phone_probe"),
                            None,
                        )
                except Exception:
                    logger.debug("phone probe harvest fail %s", page_url, exc_info=True)

    after = whatsapp_count(db)
    stats = {
        "candidates": len(candidates),
        "probed": probed,
        "live": len(live),
        "urls_added": urls_added,
        "contact_ops": contact_ops,
        "mobiles_seeded": len(mobiles),
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("yupoo_phone_probe done: %s", stats)
    return stats
