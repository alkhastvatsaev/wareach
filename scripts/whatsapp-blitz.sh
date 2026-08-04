#!/usr/bin/env bash
# WhatsApp Blitz — maximize unique +86 WhatsApp contacts toward 10,000 / week
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"
export EXA_NUM_RESULTS="${EXA_NUM_RESULTS:-15}"

ROUNDS="${1:-200}"
BATCH="${2:-25}"
WORKERS="${3:-3}"
SLEEP_SEC="${SLEEP_SEC:-45}"

echo "=== WAREACH WhatsApp Blitz ==="
echo "Target: 10,000 unique WhatsApp | rounds=$ROUNDS batch=$BATCH workers=$WORKERS"
echo "Pace needed: ~1,429 / day for 7 days"
echo ""

python - <<PY
import os, time
from app.db.session import Base, engine, SessionLocal
from app.db.migrate import ensure_schema
from app.main import upsert_search_queries
from app.services.whatsapp_harvest import run_whatsapp_blitz, whatsapp_count
from app.services.pipeline import run_crawl_batch

Base.metadata.create_all(bind=engine)
ensure_schema()
n = upsert_search_queries()
print(f"seed upserted: {n}", flush=True)

rounds = int(os.environ.get("ROUNDS", "$ROUNDS"))
batch = int(os.environ.get("BATCH", "$BATCH"))
workers = int(os.environ.get("WORKERS", "$WORKERS"))
sleep_sec = int(os.environ.get("SLEEP_SEC", "$SLEEP_SEC"))
target = 10000

for i in range(1, rounds + 1):
    db = SessionLocal()
    try:
        wa = whatsapp_count(db)
        print(f"\\n--- round {i}/{rounds} | WhatsApp={wa}/{target} remaining={max(0,target-wa)} ---", flush=True)
        if wa >= target:
            print("TARGET REACHED", flush=True)
            break
        stats = run_whatsapp_blitz(db, query_limit=batch, workers=workers)
        print("blitz:", stats, flush=True)
        # Light crawl of pending Yupoo URLs to pull more WA from pages
        crawl = run_crawl_batch(db, limit=15)
        print("crawl:", crawl, flush=True)
        # Playwright deep-dive on Yupoo pending (JS + passwords + screenshots)
        try:
            from app.services.browser_dive import run_browser_deep_dive
            dive = run_browser_deep_dive(db, limit=12, yupoo_only=True)
            print("browser_dive:", dive, flush=True)
        except Exception as be:
            print("browser_dive_skip:", be, flush=True)
        print(f"WhatsApp now: {whatsapp_count(db)}", flush=True)
    except Exception as e:
        print("ERROR", e, flush=True)
    finally:
        db.close()
    time.sleep(sleep_sec)

db = SessionLocal()
print("\\nFINAL WhatsApp:", whatsapp_count(db), flush=True)
db.close()
PY
