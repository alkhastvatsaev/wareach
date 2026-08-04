"""Discovery via Agent Reach (Exa/mcporter + Jina) + Firecrawl + Playwright."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SearchHit:
    url: str
    title: str | None = None
    snippet: str | None = None
    source: str = "exa"


def unwrap_search_redirect(url: str) -> str:
    """Turn Bing/Google/Baidu tracking URLs into the destination when possible."""
    from urllib.parse import parse_qs, unquote, urlparse
    import base64

    if not url or not url.startswith("http"):
        return url
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        qs = parse_qs(p.query)

        if "bing.com" in host:
            raw = (qs.get("u") or [None])[0]
            if raw:
                payload = raw[2:] if raw.startswith("a1") else raw
                pad = "=" * (-len(payload) % 4)
                try:
                    decoded = base64.urlsafe_b64decode(payload + pad).decode("utf-8", "ignore")
                    if decoded.startswith("http"):
                        return decoded
                except Exception:
                    pass
            for key in ("r", "url"):
                cand = (qs.get(key) or [None])[0]
                if cand and str(cand).startswith("http"):
                    return str(cand)

        if "google." in host and ("/url" in p.path or "/search" in p.path):
            for key in ("q", "url", "u"):
                cand = (qs.get(key) or [None])[0]
                if cand and str(cand).startswith("http"):
                    return unquote(str(cand))

        if "baidu.com" in host and ("url" in qs or "u" in qs):
            for key in ("url", "u"):
                cand = (qs.get(key) or [None])[0]
                if cand and str(cand).startswith("http"):
                    return unquote(str(cand))

        if "duckduckgo.com" in host:
            cand = (qs.get("uddg") or [None])[0]
            if cand and str(cand).startswith("http"):
                return unquote(str(cand))
    except Exception:
        logger.debug("unwrap_search_redirect failed for %s", url[:120], exc_info=True)
    return url


def _parse_exa_text(output: str) -> list[SearchHit]:
    hits: list[SearchHit] = []
    blocks = re.split(r"\n(?=Title:)", output)
    for block in blocks:
        title_m = re.search(r"^Title:\s*(.*)$", block, re.M)
        url_m = re.search(r"^URL:\s*(.*)$", block, re.M)
        if not url_m:
            continue
        url = url_m.group(1).strip()
        if not url.startswith("http"):
            continue
        title = title_m.group(1).strip() if title_m else None
        snip = None
        hm = re.search(r"Highlights:\s*\n([\s\S]+?)(?:\n---|\Z)", block)
        if hm:
            snip = hm.group(1).strip()[:1500]
        hits.append(SearchHit(url=url, title=title, snippet=snip, source="exa"))
    return hits


def search_exa(query: str, num_results: int | None = None) -> list[SearchHit]:
    from app.services.engine_state import is_available, mark_rate_limited

    if not is_available("exa"):
        return []
    n = num_results or settings.exa_num_results
    q = query.replace('"', '\\"')
    cmd = f'exa.web_search_exa(query: "{q}", numResults: {n})'
    import time

    for attempt in range(3):
        try:
            proc = subprocess.run(
                [settings.mcporter_bin, "call", cmd],
                capture_output=True,
                text=True,
                timeout=settings.request_timeout_sec + 30,
                check=False,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if "429" in out or "rate" in out.lower():
                mark_rate_limited("exa", 180)
                time.sleep(2.5 * (attempt + 1))
                continue
            if proc.returncode != 0 and "Title:" not in out:
                logger.warning("exa search failed rc=%s: %s", proc.returncode, out[:400])
                return []
            return _parse_exa_text(out)
        except Exception:
            logger.exception("exa search exception for %s", query)
            time.sleep(1.5)
    mark_rate_limited("exa", 120)
    return []


def search_firecrawl(query: str, limit: int = 8) -> list[SearchHit]:
    """Optional Firecrawl search via mcporter (credits permitting)."""
    try:
        proc = subprocess.run(
            [
                settings.mcporter_bin,
                "call",
                "firecrawl.firecrawl_search",
                "--args",
                json.dumps({"query": query, "limit": limit}),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        out = proc.stdout or ""
        if "402" in out or "failed" in out.lower() and "http" not in out.lower():
            return []
        hits: list[SearchHit] = []
        # Try JSON first
        try:
            start = out.find("{")
            end = out.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(out[start : end + 1])
                web = data.get("data", {}).get("web") or data.get("web") or data.get("data") or []
                if isinstance(web, dict):
                    web = web.get("results") or web.get("web") or []
                if isinstance(web, list):
                    for item in web:
                        if not isinstance(item, dict):
                            continue
                        url = item.get("url") or item.get("link")
                        if url and str(url).startswith("http"):
                            hits.append(
                                SearchHit(
                                    url=str(url),
                                    title=item.get("title"),
                                    snippet=(item.get("description") or item.get("markdown") or "")[:1200],
                                    source="firecrawl",
                                )
                            )
        except json.JSONDecodeError:
            for m in re.finditer(r"https?://[^\s\"'<>]+", out):
                hits.append(SearchHit(url=m.group(0).rstrip(".,)"), source="firecrawl"))
        return hits[:limit]
    except Exception:
        logger.debug("firecrawl search unavailable", exc_info=True)
        return []


def read_page_jina(url: str) -> str:
    from app.services.engine_state import is_available, mark_rate_limited

    if not is_available("jina"):
        return ""
    target = f"{settings.jina_reader_prefix.rstrip('/')}/{url}"
    try:
        with httpx.Client(timeout=settings.request_timeout_sec, follow_redirects=True) as client:
            r = client.get(target, headers={"Accept": "text/plain"})
            if r.status_code == 429:
                mark_rate_limited("jina", 90)
                return ""
            r.raise_for_status()
            return r.text[:200_000]
    except Exception as exc:
        msg = str(exc)
        if "429" in msg:
            mark_rate_limited("jina", 90)
        logger.warning("jina read failed %s: %s", url, exc)
        return ""


def read_page_raw(url: str) -> str:
    try:
        with httpx.Client(timeout=settings.request_timeout_sec, follow_redirects=True) as client:
            r = client.get(
                url,
                headers={
                    "User-Agent": "WAREACHBrandProtection/2.0 (+LVMH-Richemont IP enforcement OSINT)",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
            )
            r.raise_for_status()
            return r.text[:200_000]
    except Exception as exc:
        logger.warning("raw fetch failed %s: %s", url, exc)
        return ""


def read_page_playwright(url: str) -> str:
    """JS-rendered pages (Yupoo albums) when Playwright is installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="WAREACHBrandProtection/2.0 (+brand-protection OSINT)"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1500)
            text = page.inner_text("body")
            browser.close()
            return (text or "")[:200_000]
    except Exception as exc:
        logger.warning("playwright fetch failed %s: %s", url, exc)
        return ""


def fetch_page_content(url: str) -> str:
    """Prefer raw/playwright when Jina is cooling — avoid stacked 429s."""
    from app.services.engine_state import is_available

    text = ""
    if is_available("jina"):
        text = read_page_jina(url)
    if len(text) < 250 and ("yupoo" in url.lower() or "weidian" in url.lower()):
        raw = read_page_raw(url)
        if len(raw) > len(text):
            text = raw
        if len(text) < 200:
            pw = read_page_playwright(url)
            if len(pw) > len(text):
                text = pw
    if len(text) < 200:
        text = read_page_raw(url) or text
    return text


def duckduckgo_lite(query: str, max_results: int = 10) -> list[SearchHit]:
    hits: list[SearchHit] = []
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "WAREACHBrandProtection/2.0"},
            )
            r.raise_for_status()
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("a.result__a")[:max_results]:
                href = a.get("href")
                title = a.get_text(strip=True)
                if href and href.startswith("http"):
                    hits.append(SearchHit(url=href, title=title, source="ddg"))
    except Exception:
        logger.exception("ddg fallback failed")
    return hits


def bing_lite(query: str, max_results: int = 10) -> list[SearchHit]:
    """Bing HTML search — second engine when Exa rate-limits."""
    from app.services.engine_state import is_available, mark_rate_limited

    if not is_available("bing"):
        return []
    hits: list[SearchHit] = []
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                "https://www.bing.com/search",
                params={"q": query, "count": str(max_results)},
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept-Language": "en-US,en;q=0.9,zh;q=0.8",
                },
            )
            if r.status_code == 429:
                mark_rate_limited("bing", 90)
                return []
            r.raise_for_status()
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "lxml")
            for li in soup.select("li.b_algo")[:max_results]:
                a = li.select_one("h2 a")
                if not a:
                    continue
                href = a.get("href")
                title = a.get_text(strip=True)
                snip_el = li.select_one(".b_caption p") or li.select_one("p")
                snip = snip_el.get_text(" ", strip=True) if snip_el else None
                if href and str(href).startswith("http"):
                    hits.append(
                        SearchHit(
                            url=unwrap_search_redirect(str(href)),
                            title=title,
                            snippet=snip,
                            source="bing",
                        )
                    )
    except Exception:
        logger.exception("bing search failed")
    return hits


def brave_lite(query: str, max_results: int = 8) -> list[SearchHit]:
    from app.services.engine_state import is_available, mark_rate_limited

    if not is_available("brave"):
        return []
    hits: list[SearchHit] = []
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                "https://search.brave.com/search",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            )
            if r.status_code == 429:
                mark_rate_limited("brave", 300)
                return []
            r.raise_for_status()
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("a[href^='http']")[: max_results * 3]:
                href = a.get("href") or ""
                if "brave.com" in href or "microsoft.com" in href:
                    continue
                title = a.get_text(strip=True)
                if len(title) < 8:
                    continue
                hits.append(SearchHit(url=href, title=title, source="brave"))
                if len(hits) >= max_results:
                    break
    except Exception:
        logger.debug("brave search failed", exc_info=True)
    return hits


def baidu_lite(query: str, max_results: int = 8) -> list[SearchHit]:
    """Baidu HTML — China-first results (Yupoo / 水贝 often rank here)."""
    from app.services.engine_state import is_available, mark_rate_limited

    if not is_available("baidu"):
        return []
    hits: list[SearchHit] = []
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                "https://www.baidu.com/s",
                params={"wd": query, "rn": str(max_results)},
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            if r.status_code == 429:
                mark_rate_limited("baidu", 120)
                return []
            # Captcha / wappass — cool off hard
            final = str(r.url)
            body = r.text[:2000].lower()
            if "wappass.baidu.com" in final or "captcha" in body or "验证" in r.text[:1500]:
                mark_rate_limited("baidu", 300)
                logger.info("baidu captcha — cooling 5min")
                return []
            r.raise_for_status()
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("h3 a")[:max_results]:
                href = a.get("href") or ""
                title = a.get_text(strip=True)
                if not title or len(title) < 4:
                    continue
                if href.startswith("http"):
                    hits.append(SearchHit(url=href, title=title, source="baidu"))
                elif href.startswith("/link") or "baidu.com/link" in href:
                    hits.append(
                        SearchHit(
                            url=f"https://www.baidu.com{href}" if href.startswith("/") else href,
                            title=title,
                            source="baidu",
                        )
                    )
    except Exception:
        logger.debug("baidu search failed", exc_info=True)
    return hits


def discover(query: str) -> list[SearchHit]:
    """Multi-engine with cooldown: Bing/Baidu first when Exa is hot."""
    from app.services.engine_state import is_available

    hits: list[SearchHit] = []
    # Prefer free HTML engines when Exa is cooling — faster + fewer 429 loops
    if is_available("exa"):
        hits.extend(search_exa(query))
    if len(hits) < 6:
        hits.extend(bing_lite(query))
    if len(hits) < 6:
        hits.extend(baidu_lite(query))
    if len(hits) < 5:
        hits.extend(search_firecrawl(query))
    if len(hits) < 4:
        hits.extend(duckduckgo_lite(query))
    if len(hits) < 3:
        hits.extend(brave_lite(query))
    seen: set[str] = set()
    uniq: list[SearchHit] = []
    for h in hits:
        if h.url in seen:
            continue
        seen.add(h.url)
        uniq.append(h)
    return uniq
