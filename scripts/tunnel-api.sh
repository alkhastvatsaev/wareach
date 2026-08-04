#!/usr/bin/env bash
# Expose local WAREACH API via ngrok HTTPS and print the public URL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/data/logs"

if ! curl -sf -m 2 http://127.0.0.1:8000/api/ping >/dev/null; then
  echo "API down — starting watchdog…"
  nohup "$ROOT/scripts/watchdog-api.sh" >>"$ROOT/data/logs/watchdog.log" 2>&1 &
  sleep 4
fi

if ! curl -sf -m 1 http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
  echo "Starting ngrok…"
  nohup ngrok http 127.0.0.1:8000 --log=stdout >>"$ROOT/data/logs/ngrok.log" 2>&1 &
  sleep 3
fi

URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "
import sys,json
d=json.load(sys.stdin)
for t in d.get('tunnels',[]):
  u=t.get('public_url') or ''
  if u.startswith('https://'):
    print(u); break
")
if [ -z "$URL" ]; then
  echo "ngrok URL introuvable — check data/logs/ngrok.log"
  exit 1
fi

echo "PUBLIC_API=$URL"
echo "Test: curl -s -H 'ngrok-skip-browser-warning: 1' $URL/api/ping"
curl -sf -m 8 -H 'ngrok-skip-browser-warning: 1' "$URL/api/ping" && echo
