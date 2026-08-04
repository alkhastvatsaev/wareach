#!/usr/bin/env bash
# Continuous loop without Redis/Celery — ideal for Mac first run
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"

DISC_SLEEP="${DISCOVERY_INTERVAL_SEC:-180}"
CRAWL_SLEEP="${CRAWL_INTERVAL_SEC:-90}"

echo "WAREACH continuous loop (Ctrl+C to stop)"
echo "discovery every ${DISC_SLEEP}s · crawl every ${CRAWL_SLEEP}s"

python - <<'PY'
import os, time
from app.db.session import SessionLocal, Base, engine
from app.main import upsert_search_queries
from app.db.migrate import ensure_schema
from app.services.pipeline import run_discovery_batch, run_crawl_batch, stats_overview

Base.metadata.create_all(bind=engine)
ensure_schema()
upsert_search_queries()

disc_every = int(os.getenv("DISCOVERY_INTERVAL_SEC", "180"))
crawl_every = int(os.getenv("CRAWL_INTERVAL_SEC", "90"))
next_disc = 0.0
next_crawl = 0.0

while True:
    now = time.time()
    db = SessionLocal()
    try:
        if now >= next_disc:
            print("[discovery]", run_discovery_batch(db, limit=12), flush=True)
            next_disc = time.time() + disc_every
        if now >= next_crawl:
            print("[crawl]", run_crawl_batch(db, limit=20), flush=True)
            next_crawl = time.time() + crawl_every
        print("[stats]", stats_overview(db), flush=True)
    except Exception as e:
        print("[error]", e, flush=True)
    finally:
        db.close()
    time.sleep(15)
PY
