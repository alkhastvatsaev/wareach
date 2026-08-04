#!/usr/bin/env bash
# Browser deep-dive — Playwright on pending Yupoo/Weidian URLs
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"

LIMIT="${1:-20}"
echo "=== WAREACH Browser Deep-Dive (Playwright) limit=$LIMIT ==="

python - <<PY
import os
from app.db.session import Base, engine, SessionLocal
from app.db.migrate import ensure_schema
from app.services.browser_dive import run_browser_deep_dive
from app.services.whatsapp_harvest import whatsapp_count

Base.metadata.create_all(bind=engine)
ensure_schema()
limit = int(os.environ.get("LIMIT", "$LIMIT"))
db = SessionLocal()
print("WA before:", whatsapp_count(db), flush=True)
print(run_browser_deep_dive(db, limit=limit, yupoo_only=True), flush=True)
print("WA after:", whatsapp_count(db), flush=True)
db.close()
PY
