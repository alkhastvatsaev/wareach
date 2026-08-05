# LuxMatch

Marketplace photo → devis WhatsApp (séparé de WAREACH).

## Démarrage

```bash
# API WAREACH (port 8000)
cd .. && source .venv/bin/activate
export PYTHONPATH="$PWD/backend"
# optionnel: export OPENAI_API_KEY=sk-...
# optionnel: export LUXMATCH_PUBLIC_URL=http://localhost:3001
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# UI LuxMatch (port 3001)
cd luxmatch && npm install && npm run dev
```

Ouvre http://localhost:3001

## Flow

1. Drop photo → analyse IA (`OPENAI_API_KEY` ou mode mock)
2. Confirme description → RFQ + **10** WhatsApp auto (`tools/whatsapp/send-rfq.js`)
3. Vendeur ouvre `/s/{token}` → devis
4. Client `/r/{token}` → choisit → avis

## WhatsApp

Session Baileys partagée avec WAREACH (`tools/whatsapp/auth`).

```bash
cd tools/whatsapp && npm run login   # si besoin QR
```
