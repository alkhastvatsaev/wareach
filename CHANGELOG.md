# Changelog

## 0.1.1 — 2026-08-04

- Fix reach stall: purge ~5.7k Bing redirect URLs blocking the crawl queue
- Never upsert search-engine junk (`bing.com`, Google/DDG redirects); unwrap Bing tracking URLs
- Autopilot: Yupoo-first larger batches, skip dry expand, discovery refill, shorter sleep
- Cap search-engine cooldowns at 5 minutes (Baidu captcha no longer idles 30min)

## 0.1.0 — 2026-08-04

- Rebrand **WAREACH** (ex-LuxGuard)
- Autopilot harvest + WhatsApp Baileys verify
- Next.js console with Framer Motion UI
- Same-origin `/api/osint` proxy + Vercel deploy
- ngrok tunnel script for cloud → local API
