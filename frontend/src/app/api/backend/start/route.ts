import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

function projectRoot(): string {
  // Prefer monorepo root (…/wareach or …/luxguard). On Vercel cwd is frontend or repo root.
  const cwd = process.cwd();
  const candidates = [
    path.resolve(cwd, ".."),
    cwd,
    path.resolve(cwd, "../.."),
  ];
  for (const root of candidates) {
    if (fs.existsSync(path.join(root, "scripts", "watchdog-api.sh"))) return root;
    if (fs.existsSync(path.join(root, "backend", "app", "main.py"))) return root;
  }
  return path.resolve(cwd, "..");
}

function backendBase(): string {
  return (
    process.env.BACKEND_URL ||
    process.env.WAREACH_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

async function apiHealthy(): Promise<boolean> {
  try {
    // Prefer lightweight ping; fall back to stats
    for (const p of ["/api/ping", "/api/stats"]) {
      try {
        const res = await fetch(`${backendBase()}${p}`, {
          cache: "no-store",
          signal: AbortSignal.timeout(4000),
        });
        if (res.ok) return true;
      } catch {
        /* try next */
      }
    }
    return false;
  } catch {
    return false;
  }
}

export async function GET() {
  const ok = await apiHealthy();
  return NextResponse.json({
    ok,
    url: backendBase(),
    vercel: process.env.VERCEL === "1",
  });
}

export async function POST() {
  // On Vercel serverless we cannot spawn local uvicorn
  if (process.env.VERCEL === "1") {
    const ok = await apiHealthy();
    if (ok) {
      return NextResponse.json({
        ok: true,
        already_up: true,
        message: "Backend distant joignable",
      });
    }
    return NextResponse.json(
      {
        ok: false,
        vercel: true,
        error: "Pas d’API joignable depuis Vercel",
        hint:
          "Définis BACKEND_URL (HTTPS) dans Vercel, ou ouvre l’UI en local: cd frontend && npm run dev + ./scripts/start-autopilot.sh",
      },
      { status: 503 }
    );
  }

  const root = projectRoot();
  const script = path.join(root, "scripts", "watchdog-api.sh");
  if (!fs.existsSync(script)) {
    return NextResponse.json(
      {
        ok: false,
        error: `Script introuvable: ${script}`,
        hint: "Lance manuellement ./scripts/start-autopilot.sh depuis le repo",
      },
      { status: 500 }
    );
  }

  if (await apiHealthy()) {
    try {
      await fetch(`${backendBase()}/api/autopilot?enabled=true&verify_wa=true`, {
        method: "POST",
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      });
    } catch {
      /* ignore */
    }
    return NextResponse.json({
      ok: true,
      already_up: true,
      autopilot: true,
      message: "API déjà en ligne — autopilote ON",
    });
  }

  const logDir = path.join(root, "data", "logs");
  fs.mkdirSync(logDir, { recursive: true });
  const out = fs.openSync(path.join(logDir, "watchdog.log"), "a");

  const child = spawn("bash", [script], {
    cwd: root,
    detached: true,
    stdio: ["ignore", out, out],
    env: { ...process.env },
  });
  child.unref();

  let healthy = false;
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    if (await apiHealthy()) {
      healthy = true;
      break;
    }
  }

  if (healthy) {
    try {
      await fetch(`${backendBase()}/api/autopilot?enabled=true&verify_wa=true`, {
        method: "POST",
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
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
