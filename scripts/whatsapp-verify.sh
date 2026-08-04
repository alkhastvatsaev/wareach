#!/usr/bin/env bash
# Vérifie jusqu'à N contacts WhatsApp unverified via Baileys
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"
LIMIT="${1:-40}"
DELAY_MS="${DELAY_MS:-4000}"

python - <<PY
from app.db.session import SessionLocal
from app.services.wa_verify import run_whatsapp_verify, auth_ready
print("auth_ready", auth_ready())
db = SessionLocal()
try:
    print(run_whatsapp_verify(db, limit=int("$LIMIT"), delay_ms=int("$DELAY_MS")))
finally:
    db.close()
PY
