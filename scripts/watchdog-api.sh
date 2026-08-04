#!/usr/bin/env bash
# Keep WAREACH API alive — restart if health check fails.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR"
API_LOG="$LOG_DIR/api.log"
WATCH_LOG="$LOG_DIR/watchdog.log"
INTERVAL="${WATCHDOG_INTERVAL:-12}"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$WATCH_LOG"; }

is_up() {
  curl -sf -m 3 "http://127.0.0.1:8000/api/health" >/dev/null 2>&1
}

start_api() {
  # Free stale listeners that are not healthy
  if lsof -ti:8000 >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
  log "Starting API…"
  (
    cd "$ROOT"
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
    export PYTHONPATH="$ROOT/backend"
    nohup uvicorn app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000 \
      >>"$API_LOG" 2>&1 &
    echo $! >"$LOG_DIR/api.pid"
  )
  # Wait for health
  for _ in $(seq 1 20); do
    sleep 1
    if is_up; then
      log "API healthy"
      return 0
    fi
  done
  log "API failed to become healthy — check $API_LOG"
  return 1
}

log "Watchdog armed (every ${INTERVAL}s)"
if ! is_up; then
  start_api || true
fi

while true; do
  if ! is_up; then
    log "API down — restarting"
    start_api || true
  fi
  sleep "$INTERVAL"
done
