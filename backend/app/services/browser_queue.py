"""Redis-backed queue for browser deep-dive URLs (optional; falls back to DB)."""

from __future__ import annotations

import json
import logging

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
QUEUE_KEY = "wareach:browser:queue"


def _client() -> redis.Redis | None:
    try:
        r = redis.from_url(get_settings().redis_url, socket_connect_timeout=1.5)
        if r.ping():
            return r
    except Exception:
        logger.debug("redis unavailable for browser queue", exc_info=True)
    return None


def enqueue_urls(items: list[dict]) -> int:
    """items: [{id, url, title, snippet, source_query, brand_hint}]"""
    r = _client()
    if not r or not items:
        return 0
    n = 0
    for it in items:
        r.rpush(QUEUE_KEY, json.dumps(it, ensure_ascii=False))
        n += 1
    return n


def dequeue_batch(limit: int = 10) -> list[dict]:
    r = _client()
    if not r:
        return []
    out: list[dict] = []
    for _ in range(limit):
        raw = r.lpop(QUEUE_KEY)
        if not raw:
            break
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


def queue_depth() -> int:
    r = _client()
    if not r:
        return -1
    try:
        return int(r.llen(QUEUE_KEY))
    except Exception:
        return -1
