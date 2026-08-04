"""Search engine cooldown / rotation — Redis-backed so API/Celery/auto share state."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_local: dict[str, float] = {}
_KEY = "wareach:engine_cooldown"


def _redis():
    try:
        import redis
        from app.core.config import get_settings

        r = redis.from_url(get_settings().redis_url, socket_connect_timeout=1.0)
        if r.ping():
            return r
    except Exception:
        return None
    return None


def mark_rate_limited(engine: str, seconds: float = 120.0) -> None:
    # Cap so one captcha does not idle discovery for 30+ minutes
    seconds = min(float(seconds), 300.0)
    until = time.time() + seconds
    with _lock:
        _local[engine] = max(_local.get(engine, 0), until)
    r = _redis()
    if r:
        try:
            r.hset(_KEY, engine, str(until))
            r.expire(_KEY, int(max(seconds, 60)) + 3600)
        except Exception:
            logger.debug("redis cooldown write failed", exc_info=True)


def clear_cooldown(engine: str | None = None) -> None:
    with _lock:
        if engine is None:
            _local.clear()
        else:
            _local.pop(engine, None)
    r = _redis()
    if not r:
        return
    try:
        if engine is None:
            r.delete(_KEY)
        else:
            r.hdel(_KEY, engine)
    except Exception:
        logger.debug("redis cooldown clear failed", exc_info=True)


def is_available(engine: str) -> bool:
    now = time.time()
    with _lock:
        local_until = _local.get(engine, 0)
    if now < local_until:
        return False
    r = _redis()
    if r:
        try:
            raw = r.hget(_KEY, engine)
            if raw is not None:
                until = float(raw)
                with _lock:
                    _local[engine] = max(_local.get(engine, 0), until)
                return now >= until
        except Exception:
            pass
    return True


def status() -> dict[str, float]:
    now = time.time()
    out: dict[str, float] = {}
    with _lock:
        for k, v in _local.items():
            if v > now:
                out[k] = round(v - now, 1)
    r = _redis()
    if r:
        try:
            for k, v in (r.hgetall(_KEY) or {}).items():
                key = k.decode() if isinstance(k, bytes) else str(k)
                until = float(v)
                rem = until - now
                if rem > 0:
                    out[key] = max(out.get(key, 0), round(rem, 1))
        except Exception:
            pass
    return out
