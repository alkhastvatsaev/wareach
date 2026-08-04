#!/usr/bin/env bash
# Première connexion WhatsApp (scan QR) — session sauvée dans tools/whatsapp/auth/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/tools/whatsapp"
if [[ ! -d node_modules ]]; then
  echo "==> npm install"
  npm install
fi
echo "==> Scan le QR dans le terminal (WhatsApp → Appareils connectés)"
# Option: réutiliser la session avis-google
#   cp -R ~/Desktop/avis-google/tools/whatsapp/auth ./auth
node check_batch.js --login-only
