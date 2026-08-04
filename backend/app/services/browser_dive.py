"""Browser deep-dive — Playwright on Yupoo/JS pages to extract WhatsApp + evidence."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import DiscoveredUrl, JobRun
from app.services.pipeline import merge_supplier_from_extraction, utcnow
from app.services.whatsapp_harvest import whatsapp_count

logger = logging.getLogger(__name__)
settings = get_settings()

# Common Yupoo album passwords seen in OSINT catalogs
YUPOO_PASSWORD_CANDIDATES = [
    "123456",
    "888888",
    "666666",
    "000000",
    "111111",
    "yupoo",
    "vip",
    "vip888",
    "luxury",
    "bags",
    "gotashop",
    "password",
]


def _evidence_dir() -> Path:
    p = Path(settings.evidence_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _extract_password_hints(text: str) -> list[str]:
    hints: list[str] = []
    for pat in [
        r"(?:pass(?:word)?|密码|碼)\s*[:：=]\s*([A-Za-z0-9_\-]{3,20})",
        r"(?:pwd)\s*[:：=]\s*([A-Za-z0-9_\-]{3,20})",
    ]:
        for m in re.finditer(pat, text or "", re.I):
            hints.append(m.group(1))
    return hints


def browse_page(url: str, password_hints: list[str] | None = None) -> dict:
    """
    Open URL with Playwright Chromium.
    Returns {text, screenshot_path, ok, error}.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return {"text": "", "screenshot_path": None, "ok": False, "error": f"playwright missing: {exc}"}

    passwords = list(dict.fromkeys((password_hints or []) + YUPOO_PASSWORD_CANDIDATES))
    shot_path = _evidence_dir() / f"shot_{abs(hash(url)) % 10_000_000}.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
                viewport={"width": 1400, "height": 900},
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1200)

            # Yupoo password gate
            body = page.inner_text("body") if page.locator("body").count() else ""
            needs_pass = any(
                x in body.lower()
                for x in ["password", "密码", "請輸入", "请输入", "album password", "访问密码"]
            )
            if needs_pass or page.locator("input[type='password']").count() > 0:
                for pwd in passwords[:12]:
                    try:
                        inp = page.locator("input[type='password']").first
                        if inp.count() == 0:
                            inp = page.locator("input").first
                        inp.fill(pwd)
                        # submit
                        btn = page.locator("button, input[type='submit'], .btn, a").filter(
                            has_text=re.compile(r"ok|确定|確認|submit|enter|访问", re.I)
                        )
                        if btn.count() > 0:
                            btn.first.click()
                        else:
                            page.keyboard.press("Enter")
                        page.wait_for_timeout(1500)
                        body2 = page.inner_text("body")
                        if not any(x in body2.lower() for x in ["密码错误", "wrong password", "incorrect"]):
                            if len(body2) > len(body) + 80 or "whatsapp" in body2.lower():
                                body = body2
                                break
                    except Exception:
                        continue

            page.wait_for_timeout(800)
            # Expand / scroll to load lazy contact banners
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(600)
                page.evaluate("window.scrollTo(0, 0)")
            except Exception:
                pass

            text = page.inner_text("body")
            # Also pull meta / title
            title = page.title()
            text = f"{title}\n{text}"

            try:
                page.screenshot(path=str(shot_path), full_page=False)
            except Exception:
                shot_path = None  # type: ignore

            browser.close()
            return {
                "text": (text or "")[:250_000],
                "screenshot_path": str(shot_path) if shot_path else None,
                "ok": True,
                "error": None,
            }
    except Exception as exc:
        logger.warning("browse failed %s: %s", url, exc)
        return {"text": "", "screenshot_path": None, "ok": False, "error": str(exc)[:800]}


def run_browser_deep_dive(
    db: Session,
    *,
    limit: int = 20,
    yupoo_only: bool = True,
    workers: int = 3,
) -> dict:
    """
    Process pending URLs with Playwright pool — priority Yupoo — extract WA + save evidence.
    Network browse runs in threads; DB merges stay on the main session.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from app.services.browser_queue import enqueue_urls, queue_depth

    before = whatsapp_count(db)
    job = JobRun(job_type="browser_deep_dive", status="running", stats={})
    db.add(job)
    db.commit()
    db.refresh(job)

    stmt = (
        select(DiscoveredUrl)
        .where(DiscoveredUrl.status.in_(["pending", "failed"]))
        .where(DiscoveredUrl.fail_count < 4)
        .order_by(DiscoveredUrl.priority.desc(), DiscoveredUrl.discovered_at.asc())
    )
    if yupoo_only:
        stmt = stmt.where(
            or_(
                DiscoveredUrl.domain.ilike("%yupoo%"),
                DiscoveredUrl.domain.ilike("%weidian%"),
                DiscoveredUrl.domain.ilike("%wsxc%"),
                DiscoveredUrl.url.ilike("%yupoo%"),
            )
        )
    rows = list(db.scalars(stmt.limit(limit)))

    enqueue_urls(
        [
            {
                "id": r.id,
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet,
                "source_query": r.source_query,
                "brand_hint": r.brand_hint,
            }
            for r in rows
        ]
    )

    for row in rows:
        row.status = "browsing"
    db.commit()

    def _job(row: DiscoveredUrl) -> tuple[int, dict]:
        hints = _extract_password_hints(
            f"{row.title or ''}\n{row.snippet or ''}\n{row.source_query or ''}"
        )
        return row.id, browse_page(row.url, password_hints=hints)

    browse_results: dict[int, dict] = {}
    n_workers = max(1, min(workers, 4, len(rows) or 1))
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futs = [pool.submit(_job, row) for row in rows]
        for fut in as_completed(futs):
            try:
                rid, result = fut.result()
                browse_results[rid] = result
            except Exception as exc:
                logger.warning("browser worker failed: %s", exc)

    browsed = 0
    wa_pages = 0
    contacts = 0
    failed = 0
    screenshots = 0
    by_id = {r.id: r for r in rows}

    for rid, result in browse_results.items():
        row = by_id.get(rid)
        if not row:
            continue
        if not result.get("ok") or len(result.get("text") or "") < 40:
            failed += 1
            row.status = "failed"
            row.fail_count = (row.fail_count or 0) + 1
            row.last_error = result.get("error") or "empty_page"
            continue

        browsed += 1
        if result.get("screenshot_path"):
            screenshots += 1

        seed = "\n".join(filter(None, [row.title, row.snippet, row.url]))
        text = f"{seed}\n{result['text']}"
        if "whatsapp" in text.lower() or "+86" in text:
            wa_pages += 1

        info = merge_supplier_from_extraction(
            db,
            url=row.url,
            title=row.title,
            text=text,
            brand_hint=row.brand_hint,
        )
        contacts += int(info.get("contacts") or 0)

        row.status = "done"
        row.crawled_at = utcnow()
        row.last_error = None
        if result.get("screenshot_path"):
            note = f"[evidence:{result['screenshot_path']}]"
            if row.snippet and note not in row.snippet:
                row.snippet = (row.snippet or "")[:1400] + " " + note
            elif not row.snippet:
                row.snippet = note

    for row in rows:
        if row.id not in browse_results and row.status == "browsing":
            row.status = "failed"
            row.fail_count = (row.fail_count or 0) + 1
            row.last_error = "worker_no_result"
            failed += 1

    db.commit()
    after = whatsapp_count(db)
    stats = {
        "batch": len(rows),
        "browsed": browsed,
        "failed": failed,
        "pages_with_wa_signal": wa_pages,
        "contacts_ops": contacts,
        "screenshots": screenshots,
        "whatsapp_before": before,
        "whatsapp_after": after,
        "whatsapp_gained": max(0, after - before),
        "yupoo_only": yupoo_only,
        "workers": n_workers,
        "redis_queue_depth": queue_depth(),
    }
    job.status = "done"
    job.finished_at = utcnow()
    job.stats = stats
    db.commit()
    logger.info("browser deep-dive done: %s", stats)
    return stats
