#!/usr/bin/env node
/**
 * LuxMatch — send RFQ WhatsApp messages via Baileys (max 10).
 *
 * pending_rfq.json: [{ outreach_id, phone, message }, ...]
 * rfq_results.json: [{ outreach_id, phone, ok, error? }, ...]
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
const PENDING = process.env.WA_RFQ_PENDING || path.join(DATA_DIR, "pending_rfq.json");
const RESULTS = process.env.WA_RFQ_RESULTS || path.join(DATA_DIR, "rfq_results.json");
const DELAY_MS = Number(process.env.DELAY_MS || 10000);
const MAX_SEND = Number(process.env.MAX_SEND || 10);

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function toWaDigits(raw) {
  if (!raw) return null;
  let s = String(raw).trim().replace(/[^\d+]/g, "");
  if (s.startsWith("00")) s = s.slice(2);
  if (s.startsWith("+")) s = s.slice(1);
  if (/^0[67]\d{8}$/.test(s)) s = "33" + s.slice(1);
  if (/^1[3-9]\d{9}$/.test(s)) s = "86" + s;
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
      console.log("\n[ok] WhatsApp connecté (send-rfq).\n");
      resolve(sock);
    };
    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error("Timeout connexion WA 3 min"));
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
      });
      sock.ev.on("creds.update", saveCreds);
      sock.ev.on("connection.update", async (u) => {
        const { connection, lastDisconnect, qr } = u;
        if (qr) {
          console.log("\n=== Scanne ce QR ===\n");
          qrcode.generate(qr, { small: true });
        }
        if (connection === "open") {
          finishOk(sock);
          return;
        }
        if (connection === "close") {
          const err = lastDisconnect?.error;
          const code = err instanceof Boom ? err.output?.statusCode : err?.output?.statusCode;
          if (code === 515 || code === DisconnectReason.restartRequired) {
            console.log("[info] restart session…");
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
          if (!settled) {
            settled = true;
            clearTimeout(timer);
            reject(new Error(`WA closed code=${code}`));
          }
        }
      });
    }
    start().catch(reject);
  });
}

async function main() {
  if (!fs.existsSync(PENDING)) {
    console.error("missing", PENDING);
    process.exit(1);
  }
  const items = JSON.parse(fs.readFileSync(PENDING, "utf8"));
  if (!Array.isArray(items) || !items.length) {
    fs.writeFileSync(RESULTS, "[]");
    console.log("nothing to send");
    process.exit(0);
  }
  const batch = items.slice(0, MAX_SEND);
  console.log(`[rfq] sending ${batch.length} messages…`);
  const sock = await connectWhatsApp();
  const results = [];
  for (const item of batch) {
    const digits = toWaDigits(item.phone);
    const outreachId = item.outreach_id;
    if (!digits) {
      results.push({ outreach_id: outreachId, phone: item.phone, ok: false, error: "bad_phone" });
      continue;
    }
    const jid = `${digits}@s.whatsapp.net`;
    try {
      await sock.sendMessage(jid, { text: String(item.message || "").slice(0, 3500) });
      console.log(`[sent] ${digits}`);
      results.push({ outreach_id: outreachId, phone: item.phone, ok: true });
    } catch (e) {
      console.warn(`[fail] ${digits}`, e?.message || e);
      results.push({
        outreach_id: outreachId,
        phone: item.phone,
        ok: false,
        error: String(e?.message || e).slice(0, 200),
      });
    }
    await sleep(DELAY_MS);
  }
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(RESULTS, JSON.stringify(results, null, 2));
  console.log(`[done] wrote ${RESULTS}`);
  try {
    sock.end?.(undefined);
  } catch {
    /* ignore */
  }
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  try {
    const items = JSON.parse(fs.readFileSync(PENDING, "utf8"));
    const results = (Array.isArray(items) ? items : []).slice(0, MAX_SEND).map((item) => ({
      outreach_id: item.outreach_id,
      phone: item.phone,
      ok: false,
      error: String(e?.message || e).slice(0, 200),
    }));
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(RESULTS, JSON.stringify(results, null, 2));
  } catch {
    /* ignore */
  }
  process.exit(1);
});
