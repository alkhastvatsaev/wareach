#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp -n .env.example .env 2>/dev/null || true

source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"

# Optional infra (Postgres/Redis) if Docker/Colima is up and USE_SQLITE=false
if grep -q 'USE_SQLITE=false' "$ROOT/.env" 2>/dev/null; then
  echo "==> Starting Postgres + Redis"
  docker-compose up -d postgres redis 2>/dev/null || docker compose up -d postgres redis || true
fi

# Kill stale API on same port
if lsof -ti:8000 >/dev/null 2>&1; then
  echo "==> Freeing port 8000"
  lsof -ti:8000 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo "==> WAREACH API on http://127.0.0.1:8000 (SQLite by default on Mac)"
# No --reload: avoids killing API mid-harvest / mid-verify
exec uvicorn app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000
