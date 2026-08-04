# WAREACH

WhatsApp / WeChat OSINT for brand protection. Autopilot harvest + verify.

## Quick start

```bash
./scripts/start-autopilot.sh   # API + watchdog + autopilot
cd frontend && npm run dev     # UI → http://localhost:3000
```

## Stack

- **Frontend**: Next.js (Vercel)
- **API**: FastAPI + SQLite (local / your server)
- **WhatsApp verify**: Baileys (local session)

Set `NEXT_PUBLIC_API_URL` to your API base (default `http://127.0.0.1:8000`).
