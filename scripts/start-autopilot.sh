#!/usr/bin/env bash
# Full autopilot boot: API + watchdog (+ Celery if Redis is up)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
mkdir -p "$ROOT/data/logs"

echo "==> WAREACH AUTOPILOT"

# Optional Redis for Celery (not required — in-process autopilot covers harvest)
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
  echo "==> Redis OK — starting Celery worker+beat in background"
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
  export PYTHONPATH="$ROOT/backend"
  pkill -f 'celery -A app.celery_app' 2>/dev/null || true
  nohup celery -A app.celery_app.celery_app worker --beat --loglevel=INFO --concurrency=2 \
    >>"$ROOT/data/logs/celery.log" 2>&1 &
  echo $! >"$ROOT/data/logs/celery.pid"
else
  echo "==> Redis offline — in-process autopilot only (OK)"
fi

# Kill old watchdog then start fresh
pkill -f 'watchdog-api.sh' 2>/dev/null || true
nohup "$ROOT/scripts/watchdog-api.sh" >>"$ROOT/data/logs/watchdog.log" 2>&1 &
echo $! >"$ROOT/data/logs/watchdog.pid"

# Ensure autopilot flag ON once API is up
for _ in $(seq 1 25); do
  if curl -sf -m 2 "http://127.0.0.1:8000/api/health" >/dev/null; then
    curl -sf -m 5 -X POST "http://127.0.0.1:8000/api/autopilot?enabled=true&verify_wa=true" >/dev/null || true
    echo "==> Autopilot ON — http://127.0.0.1:8000  ·  UI http://localhost:3000"
    curl -s "http://127.0.0.1:8000/api/autopilot" || true
    echo
    exit 0
  fi
  sleep 1
done

echo "==> Waiting for API… watchdog will keep trying. Logs: data/logs/"
exit 0
