import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

function backendBase(): string {
  return (
    process.env.BACKEND_URL ||
    process.env.WAREACH_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

async function proxy(req: NextRequest, pathParts: string[]) {
  const targetPath = pathParts.join("/");
  const url = new URL(req.url);
  const dest = `${backendBase()}/api/${targetPath}${url.search}`;

  const headers = new Headers();
  const ct = req.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  headers.set("accept", req.headers.get("accept") || "application/json");

  let body: ArrayBuffer | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await req.arrayBuffer();
  }

  try {
    const upstream = await fetch(dest, {
      method: req.method,
      headers,
      body: body && body.byteLength > 0 ? body : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(280_000),
    });

    const outHeaders = new Headers();
    const pass = ["content-type", "content-disposition", "cache-control"];
    for (const h of pass) {
      const v = upstream.headers.get(h);
      if (v) outHeaders.set(h, v);
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: outHeaders,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "upstream_unreachable";
    return NextResponse.json(
      {
        ok: false,
        error: "API backend unreachable",
        detail: message,
        backend: backendBase(),
        hint:
          process.env.VERCEL === "1"
            ? "Sur Vercel, définis BACKEND_URL (HTTPS public). En local: ./scripts/start-autopilot.sh + npm run dev"
            : "Lance ./scripts/start-autopilot.sh puis clique Connecter l’API",
      },
      { status: 503 }
    );
  }
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
