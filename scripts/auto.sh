#!/usr/bin/env bash
# Blitz-only loop — Celery owns crawl/drain to avoid Jina double-hit
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"
SLEEP_SEC="${SLEEP_SEC:-50}"

echo "WAREACH AUTO (blitz+offline) — Celery handles crawl — Ctrl+C to stop"
python - <<PY
import time, os
from app.db.session import Base, engine, SessionLocal
from app.db.migrate import ensure_schema
from app.main import upsert_search_queries
from app.services.whatsapp_harvest import run_whatsapp_blitz, whatsapp_count
from app.services.reharvest import reharvest_pending_snippets
from app.services.offline_harvest import offline_harvest_all
from app.services.quality import dedup_whatsapp_variants
from app.services.pace import contact_pace
from app.services.alerts import evaluate_alerts
from app.services.engine_state import status as engine_cooldowns
from app.services.pipeline import stats_overview

Base.metadata.create_all(bind=engine)
ensure_schema()
upsert_search_queries()
sleep_sec = int(os.getenv("SLEEP_SEC", "50"))
target = 10000

while True:
    db = SessionLocal()
    try:
        wa = whatsapp_count(db)
        pace = contact_pace(db)
        alerts = evaluate_alerts(db)
        top = (alerts.get("alerts") or [{}])[0].get("message", "")
        print(
            f"\\nWA {wa}/{target} | {pace.get('wa_per_hour')}/h | ETA {pace.get('eta_hours_to_10k_wa')}h | cool={engine_cooldowns()}",
            flush=True,
        )
        if top:
            print("ALERT", top, flush=True)
        if wa >= target:
            print("DONE", flush=True)
            break
        print("offline", offline_harvest_all(db, limit=5000), flush=True)
        print("expand", __import__("app.services.yupoo_expand", fromlist=["run_yupoo_expand"]).run_yupoo_expand(db, seed_limit=25), flush=True)
        print("yupoo_raw", __import__("app.services.yupoo_raw", fromlist=["run_yupoo_raw_crawl"]).run_yupoo_raw_crawl(db, limit=40, workers=6), flush=True)
        print("blitz", run_whatsapp_blitz(db, query_limit=18, workers=3), flush=True)
        print("reharvest", reharvest_pending_snippets(db, limit=800), flush=True)
        print("dedup", dedup_whatsapp_variants(db), flush=True)
        s = stats_overview(db)
        print("stats", {k: s.get(k) for k in ("whatsapp", "wechat", "urls_pending", "wa_per_hour")}, flush=True)
    finally:
        db.close()
    time.sleep(sleep_sec)
PY
