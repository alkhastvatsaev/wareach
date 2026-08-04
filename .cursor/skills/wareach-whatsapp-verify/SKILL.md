---
name: wareach-whatsapp-verify
description: >-
  Vérifie si des contacts WhatsApp WAREACH existent vraiment (Baileys onWhatsApp,
  sans envoyer de message). À utiliser quand l'utilisateur demande de vérifier,
  valider, ou checker des numéros WA / +86, ou de brancher la feature avis-google.
---

# WAREACH — vérification WhatsApp (Baileys)

## Origine

Porté depuis `~/Desktop/avis-google/tools/whatsapp/check.js` (feature « vérifier numéro WhatsApp »).

## Principe

- Utilise **Baileys** `sock.onWhatsApp(digits)` — **aucun message envoyé**.
- Résultats mappés : `oui` → `reachable`, `non`/`invalide` → `dead`.
- Session QR dans `wareach/tools/whatsapp/auth/` (ne jamais committer).

## Setup (une fois)

```bash
cd wareach/tools/whatsapp && npm install
./scripts/whatsapp-login.sh          # scan QR dans le terminal
# OU réutiliser la session avis-google :
# cp -R ~/Desktop/avis-google/tools/whatsapp/auth wareach/tools/whatsapp/auth
```

## Lancer une vague

```bash
./scripts/whatsapp-verify.sh 40      # 40 contacts unverified
# ou API :
curl -X POST 'http://127.0.0.1:8000/api/jobs/whatsapp-verify?limit=40'
curl http://127.0.0.1:8000/api/whatsapp-verify/status
```

UI : bouton **Vérifier WhatsApp** sur http://localhost:3000

## Fichiers clés

| Path | Rôle |
|------|------|
| `tools/whatsapp/check_batch.js` | Worker Node Baileys (+86 CN + FR) |
| `backend/app/services/wa_verify.py` | Export pending → node → import DB |
| `scripts/whatsapp-login.sh` | QR login |
| `scripts/whatsapp-verify.sh` | Batch CLI |

## Règles ops

- Délai défaut **4s** entre checks (`DELAY_MS`) — ne pas spam.
- Plafond session `MAX_CHECKS` / `limit` API.
- Si « Logged out » : supprimer `tools/whatsapp/auth/` et rescanner.
- Code 515 après QR = normal (restart session).
- Ne jamais mass-message les numéros ; cette feature = existence only.

## Quand l'agent doit l'utiliser

- User: « vérifie les WhatsApp », « check si les numéros sont vivants », « lance Baileys »
- Après une grosse récolte : proposer une vague verify sur les unverified
- Si `auth_ready=false` : guider vers `whatsapp-login.sh` avant le batch
