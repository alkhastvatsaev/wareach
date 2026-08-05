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
  const dest = `${backendBase()}/api/luxmatch/${targetPath}${url.search}`;

  const headers = new Headers();
  const ct = req.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  headers.set("accept", req.headers.get("accept") || "*/*");
  headers.set("ngrok-skip-browser-warning", "1");

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
    for (const h of ["content-type", "content-disposition", "cache-control"]) {
      const v = upstream.headers.get(h);
      if (v) outHeaders.set(h, v);
    }
    return new NextResponse(upstream.body, { status: upstream.status, headers: outHeaders });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: "API unreachable", detail: err instanceof Error ? err.message : "err" },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PUT(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
export async function PATCH(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
