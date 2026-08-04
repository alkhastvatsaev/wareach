import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function luxRoot(): string {
  // frontend/ → wareach/
  return path.resolve(process.cwd(), "..");
}

async function apiHealthy(): Promise<boolean> {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/health", {
      cache: "no-store",
      signal: AbortSignal.timeout(2500),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function GET() {
  const ok = await apiHealthy();
  return NextResponse.json({ ok, url: "http://127.0.0.1:8000" });
}

export async function POST() {
  const root = luxRoot();
  const script = path.join(root, "scripts", "watchdog-api.sh");
  if (!fs.existsSync(script)) {
    return NextResponse.json(
      { ok: false, error: `Script introuvable: ${script}` },
      { status: 500 }
    );
  }

  // If already healthy, just re-enable autopilot
  if (await apiHealthy()) {
    try {
      await fetch("http://127.0.0.1:8000/api/autopilot?enabled=true&verify_wa=true", {
        method: "POST",
        cache: "no-store",
      });
    } catch {
      /* ignore */
    }
    return NextResponse.json({ ok: true, already_up: true, autopilot: true });
  }

  const logDir = path.join(root, "data", "logs");
  fs.mkdirSync(logDir, { recursive: true });
  const out = fs.openSync(path.join(logDir, "watchdog.log"), "a");

  // Detach watchdog so it keeps API alive
  const child = spawn("bash", [script], {
    cwd: root,
    detached: true,
    stdio: ["ignore", out, out],
    env: { ...process.env },
  });
  child.unref();

  // Poll until healthy (max ~25s)
  let healthy = false;
  for (let i = 0; i < 25; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    if (await apiHealthy()) {
      healthy = true;
      break;
    }
  }

  if (healthy) {
    try {
      await fetch("http://127.0.0.1:8000/api/autopilot?enabled=true&verify_wa=true", {
        method: "POST",
        cache: "no-store",
      });
    } catch {
      /* ignore */
    }
  }

  return NextResponse.json({
    ok: healthy,
    started: true,
    pid: child.pid ?? null,
    message: healthy
      ? "API reconnectée — autopilote ON"
      : "Démarrage lancé — réessaie dans quelques secondes",
  });
}
