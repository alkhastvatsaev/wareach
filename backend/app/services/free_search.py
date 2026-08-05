"""Free / open-source search stack — no Firecrawl credits required.

Engines (in priority order for consumer OSINT):
  1. Reddit public JSON API (old.reddit.com)
  2. SearXNG public instances (meta-search, GitHub: searxng/searxng)
  3. DuckDuckGo HTML lite
  4. Brave Search HTML lite
  5. Bing HTML lite (when not captcha-blocked)
  6. Jina Reader for page text (r.jina.ai — free tier)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import quote_plus, urlparse

import httpx

from app.services.discovery import SearchHit, bing_lite, brave_lite, duckduckgo_lite, unwrap_search_redirect

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Rotating public SearXNG instances (no API key). See https://github.com/searxng/searxng
SEARX_INSTANCES = [
    "https://search.bus-hit.me",
    "https://searx.be",
    "https://search.sapti.me",
    "https://paulgo.io",
    "https://search.ononoki.org",
]


@dataclass
class RedditPost:
    author: str
    subreddit: str
    title: str
    selftext: str
    permalink: str
    url: str
    score: int
    num_comments: int
    created_utc: float


def reddit_search(query: str, *, limit: int = 25, sort: str = "relevance") -> list[RedditPost]:
    """Reddit via PullPush (free) then public JSON fallback."""
    posts = _reddit_pullpush(query, limit=limit)
    if posts:
        return posts
    return _reddit_json(query, limit=limit, sort=sort)


def _reddit_pullpush(query: str, *, limit: int = 25) -> list[RedditPost]:
    """https://github.com/Watchful1/PullPush — free Reddit search archive API."""
    posts: list[RedditPost] = []
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            r = client.get(
                "https://api.pullpush.io/reddit/search/submission/",
                params={"q": query, "size": min(limit, 100), "sort": "desc", "sort_type": "score"},
                headers={"User-Agent": UA},
            )
            if r.status_code != 200:
                return []
            data = r.json()
            for d in data.get("data") or []:
                author = str(d.get("author") or "")
                if not author or author.lower() in {"[deleted]", "automoderator"}:
                    continue
                permalink = str(d.get("permalink") or "")
                if permalink and not permalink.startswith("http"):
                    permalink = f"https://www.reddit.com{permalink}"
                posts.append(
                    RedditPost(
                        author=author,
                        subreddit=str(d.get("subreddit") or ""),
                        title=str(d.get("title") or ""),
                        selftext=str(d.get("selftext") or "")[:4000],
                        permalink=permalink,
                        url=str(d.get("url") or permalink),
                        score=int(d.get("score") or 0),
                        num_comments=int(d.get("num_comments") or 0),
                        created_utc=float(d.get("created_utc") or 0),
                    )
                )
    except Exception:
        logger.debug("pullpush reddit failed for %s", query[:80], exc_info=True)
    return posts


def _reddit_json(query: str, *, limit: int = 25, sort: str = "relevance") -> list[RedditPost]:
    """Reddit public JSON — often 403 without OAuth."""
    posts: list[RedditPost] = []
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            r = client.get(
                "https://old.reddit.com/search.json",
                params={"q": query, "limit": str(min(limit, 100)), "sort": sort, "type": "link"},
                headers={"User-Agent": UA},
            )
            if r.status_code in {403, 429}:
                return []
            r.raise_for_status()
            data = r.json()
            for child in (data.get("data") or {}).get("children") or []:
                d = (child or {}).get("data") or {}
                author = str(d.get("author") or "")
                if not author or author.lower() in {"[deleted]", "automoderator"}:
                    continue
                posts.append(
                    RedditPost(
                        author=author,
                        subreddit=str(d.get("subreddit") or ""),
                        title=str(d.get("title") or ""),
                        selftext=str(d.get("selftext") or "")[:4000],
                        permalink=f"https://www.reddit.com{d.get('permalink', '')}",
                        url=str(d.get("url") or ""),
                        score=int(d.get("score") or 0),
                        num_comments=int(d.get("num_comments") or 0),
                        created_utc=float(d.get("created_utc") or 0),
                    )
                )
    except Exception:
        logger.debug("reddit json failed for %s", query[:80], exc_info=True)
    return posts


def searx_search(query: str, *, max_results: int = 15) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for base in SEARX_INSTANCES:
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                r = client.get(
                    f"{base.rstrip('/')}/search",
                    params={"q": query, "format": "json", "language": "fr-FR"},
                    headers={"User-Agent": UA, "Accept": "application/json"},
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in (data.get("results") or [])[:max_results]:
                    url = item.get("url") or ""
                    if not url.startswith("http"):
                        continue
                    hits.append(
                        SearchHit(
                            url=unwrap_search_redirect(url),
                            title=item.get("title"),
                            snippet=(item.get("content") or "")[:1200],
                            source="searx",
                        )
                    )
                if hits:
                    return hits
        except Exception:
            continue
    return hits


def free_web_search(query: str, *, max_results: int = 12) -> list[SearchHit]:
    """Aggregate free HTML/meta search engines — Firecrawl-free."""
    hits: list[SearchHit] = []
    seen: set[str] = set()

    def add(batch: list[SearchHit]) -> None:
        for h in batch:
            u = (h.url or "").strip()
            if not u or u in seen:
                continue
            seen.add(u)
            hits.append(h)

    # Reddit site-restricted queries handled separately in demand_discovery
    add(searx_search(query, max_results=max_results))
    if len(hits) < max_results // 2:
        add(duckduckgo_lite(query, max_results=max_results))
    if len(hits) < max_results // 2:
        add(brave_lite(query, max_results=max_results))
    if len(hits) < 4:
        add(bing_lite(query, max_results=max_results))
    return hits[:max_results]


def read_page_free(url: str, *, max_chars: int = 25000) -> str:
    """Jina Reader (free HTTP) then raw GET fallback."""
    if not url.startswith("http"):
        return ""
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            r = client.get(
                f"https://r.jina.ai/{url}",
                headers={"Accept": "text/plain", "User-Agent": UA},
            )
            if r.status_code == 200 and len(r.text) > 80:
                return r.text[:max_chars]
    except Exception:
        pass
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"})
            if r.status_code < 400:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(r.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text("\n", strip=True)[:max_chars]
    except Exception:
        logger.debug("raw page read failed %s", url[:80], exc_info=True)
    return ""


def platform_from_url(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    if "reddit.com" in host:
        return "reddit"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "t.me" in host or "telegram" in host:
        return "telegram"
    if "discord" in host:
        return "discord"
    if "tiktok.com" in host:
        return "tiktok"
    if "instagram.com" in host:
        return "instagram"
    return "web"
