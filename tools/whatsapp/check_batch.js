#!/usr/bin/env node
/**
 * WAREACH — vérifie des numéros WhatsApp via Baileys (aucun message envoyé).
 * Adapté depuis avis-google/tools/whatsapp/check.js pour +86 Chine + batch JSON.
 *
 * Usage:
 *   node check_batch.js                  # lit data/pending.json → data/results.json
 *   node check_batch.js --login-only     # QR session seulement
 *   DELAY_MS=4000 MAX_CHECKS=80 node check_batch.js
 *
 * pending.json: [{ "id": 123, "phone": "+8613812345678" }, ...]
 * results.json: [{ "id", "phone", "digits", "whatsapp": "oui"|"non"|"invalide"|"erreur", "jid": "" }]
 */
import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  Browsers,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import qrcode from "qrcode-terminal";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import pino from "pino";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = process.env.WA_AUTH_DIR || path.join(__dirname, "auth");
const DATA_DIR = path.join(__dirname, "data");
const PENDING = process.env.WA_PENDING || path.join(DATA_DIR, "pending.json");
const RESULTS = process.env.WA_RESULTS || path.join(DATA_DIR, "results.json");
const DELAY_MS = Number(process.env.DELAY_MS || 4000);
const MAX_CHECKS = Number(process.env.MAX_CHECKS || 80);
const LOGIN_ONLY = process.argv.includes("--login-only");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Normalize to WhatsApp digits (country code, no +). CN + FR. */
export function toWaDigits(raw) {
  if (!raw) return null;
  let s = String(raw).trim().replace(/[^\d+]/g, "");
  if (s.startsWith("00")) s = s.slice(2);
  if (s.startsWith("+")) s = s.slice(1);
  // France mobile
  if (/^0[67]\d{8}$/.test(s)) s = "33" + s.slice(1);
  // China mobile without country code
  if (/^1[3-9]\d{9}$/.test(s)) s = "86" + s;
  // Already 86 + 11-digit mobile
  if (/^861[3-9]\d{9}$/.test(s)) return s;
  if (!/^\d{10,15}$/.test(s)) return null;
  return s;
}

function connectWhatsApp() {
  return new Promise(async (resolve, reject) => {
    let settled = false;

    const finishOk = (sock) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      console.log("\n[ok] WhatsApp connecté.\n");
      resolve(sock);
    };

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(
          new Error(
            "Timeout 3 min. Sur le téléphone annule « Logging in… », puis relance et rescane."
          )
        );
      }
    }, 180000);

    async function start() {
      fs.mkdirSync(AUTH_DIR, { recursive: true });
      const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
      const { version } = await fetchLatestBaileysVersion();

      const sock = makeWASocket({
        version,
        auth: state,
        logger: pino({ level: "silent" }),
        printQRInTerminal: false,
        browser: Browsers.macOS("Chrome"),
        syncFullHistory: false,
        markOnlineOnConnect: false,
        generateHighQualityLinkPreview: false,
      });
      sock.ev.on("creds.update", saveCreds);

      sock.ev.on("connection.update", async (u) => {
        const { connection, lastDisconnect, qr } = u;

        if (qr) {
          console.log(
            "\n=== Scanne ce QR MAINTENANT ===\nWhatsApp → ⋮ → Appareils connectés → Connecter un appareil\n"
          );
          qrcode.generate(qr, { small: true });
        }

        if (connection === "open") {
          finishOk(sock);
          return;
        }

        if (connection === "close") {
          const err = lastDisconnect?.error;
          const code =
            err instanceof Boom
              ? err.output?.statusCode
              : err?.output?.statusCode;
          console.warn(`[warn] connexion fermée code=${code}`);

          if (code === 515 || code === DisconnectReason.restartRequired) {
            console.log("[info] Redémarrage session (normal après QR)…");
            await sleep(1200);
            try {
              await start();
            } catch (e) {
              if (!settled) {
                settled = true;
                clearTimeout(timer);
                reject(e);
              }
            }
            return;
          }

          if (code === DisconnectReason.loggedOut) {
            if (!settled) {
              settled = true;
              clearTimeout(timer);
              reject(new Error("Logged out. Supprime tools/whatsapp/auth/ et relance."));
            }
            return;
          }

          if (!settled) {
            console.log("[info] Nouvelle tentative de connexion…");
            await sleep(2000);
            try {
              await start();
            } catch {
              /* timer */
            }
          }
        }
      });
    }

    try {
      await start();
    } catch (e) {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        reject(e);
      }
    }
  });
}

function loadPending() {
  if (!fs.existsSync(PENDING)) {
    return [];
  }
  const raw = JSON.parse(fs.readFileSync(PENDING, "utf8"));
  if (!Array.isArray(raw)) throw new Error("pending.json must be an array");
  return raw;
}

function saveResults(rows) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(RESULTS, JSON.stringify(rows, null, 2), "utf8");
  console.log(`[save] ${RESULTS} (${rows.length} rows)`);
}

async function main() {
  console.log(`[wareach-wa] auth=${AUTH_DIR}`);
  console.log(`[wareach-wa] delay=${DELAY_MS}ms max=${MAX_CHECKS}`);

  const sock = await connectWhatsApp();
  if (LOGIN_ONLY) {
    console.log("[done] Session OK — tu peux lancer un batch.");
    process.exit(0);
  }

  const pending = loadPending();
  if (!pending.length) {
    console.log("[check] pending vide — rien à faire.");
    saveResults([]);
    process.exit(0);
  }

  const results = [];
  let yes = 0;
  let no = 0;
  let err = 0;
  let checked = 0;

  for (let i = 0; i < pending.length; i++) {
    if (checked >= MAX_CHECKS) {
      console.log(`[check] plafond MAX_CHECKS=${MAX_CHECKS}`);
      break;
    }
    const row = pending[i];
    const digits = toWaDigits(row.phone || row.normalized_value || row.value);
    if (!digits) {
      results.push({
        id: row.id ?? null,
        phone: row.phone || "",
        digits: "",
        whatsapp: "invalide",
        jid: "",
      });
      err++;
      console.log(`[${i + 1}/${pending.length}] invalide: ${row.phone}`);
      continue;
    }

    try {
      const res = await sock.onWhatsApp(digits);
      const hit = Array.isArray(res) ? res[0] : null;
      const exists = Boolean(hit?.exists);
      const whatsapp = exists ? "oui" : "non";
      results.push({
        id: row.id ?? null,
        phone: row.phone || digits,
        digits,
        whatsapp,
        jid: exists ? hit.jid || "" : "",
      });
      if (exists) yes++;
      else no++;
      checked++;
      console.log(`[${i + 1}/${pending.length}] ${digits} → ${whatsapp}`);
    } catch (e) {
      results.push({
        id: row.id ?? null,
        phone: row.phone || digits,
        digits,
        whatsapp: "erreur",
        jid: "",
        error: String(e.message || e).slice(0, 200),
      });
      err++;
      console.warn(`[${i + 1}/${pending.length}] ${digits} erreur: ${e.message}`);
    }

    saveResults(results);
    await sleep(DELAY_MS);
  }

  saveResults(results);
  console.log(`\n[done] oui=${yes} non=${no} erreur=${err} checked=${checked}`);
  console.log("Aucun message envoyé.");
  process.exit(0);
}

main().catch((e) => {
  console.error("\n[fatal]", e.message || e);
  process.exit(1);
});
