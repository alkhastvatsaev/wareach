#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"

echo "Running one discovery + crawl cycle (sync, no Celery required)..."
python - <<'PY'
from app.db.session import SessionLocal, Base, engine
from app.main import upsert_search_queries
from app.services.pipeline import run_discovery_batch, run_crawl_batch, stats_overview

Base.metadata.create_all(bind=engine)
from app.db.migrate import ensure_schema
ensure_schema()
upsert_search_queries()
db = SessionLocal()
print("discovery:", run_discovery_batch(db, limit=8))
print("crawl:", run_crawl_batch(db, limit=15))
print("stats:", stats_overview(db))
db.close()
PY
