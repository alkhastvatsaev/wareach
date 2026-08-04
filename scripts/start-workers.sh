#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
export PYTHONPATH="$ROOT/backend"
cp -n .env.example .env 2>/dev/null || true

echo "==> Celery worker + beat (continuous discovery/crawl loops)"
celery -A app.celery_app.celery_app worker --beat --loglevel=INFO --concurrency=4
