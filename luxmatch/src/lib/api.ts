/**
 * LuxMatch client → same-origin proxy `/api/luxmatch/*` → WAREACH `/api/luxmatch/*`
 */

const API = "/api/luxmatch";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { ...init, cache: "no-store" });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const j = await res.json();
      detail = j?.detail || j?.error || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export type AiDescription = {
  brand?: string;
  model?: string;
  category?: string;
  color?: string;
  material?: string;
  summary?: string;
  confidence?: number;
  mock?: boolean;
};

export const luxmatchApi = {
  analyze: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API}/analyze`, { method: "POST", body: fd, cache: "no-store" });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      throw new Error(j?.detail || `${res.status}`);
    }
    return res.json() as Promise<{
      ok: boolean;
      request_id: number;
      client_token: string;
      photo_url: string;
      ai_description: AiDescription;
    }>;
  },
  confirm: (body: {
    request_id: number;
    user_edit?: string;
    contact_email?: string;
    contact_telegram?: string;
  }) =>
    api<{
      ok: boolean;
      client_token: string;
      client_url: string;
      status: string;
      blast_error?: string | null;
      outreach_queued: number;
    }>("/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...body, start_blast: true }),
    }),
  client: (token: string) => api<Record<string, unknown>>(`/r/${token}`),
  supplier: (token: string) => api<Record<string, unknown>>(`/s/${token}`),
  quote: (
    token: string,
    body: {
      price: number;
      currency?: string;
      description?: string;
      shipping?: string;
      payment_methods?: string[];
    }
  ) =>
    api(`/s/${token}/quote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  select: (token: string, quote_id: number) =>
    api(`/r/${token}/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quote_id }),
    }),
  review: (token: string, rating: number, comment?: string) =>
    api(`/r/${token}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating, comment }),
    }),
  photoUrl: (path: string) => {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    // proxied: /api/luxmatch/uploads/...
    if (path.startsWith("/api/luxmatch")) return path;
    return `${API}${path.replace(/^\/api\/luxmatch/, "")}`;
  },
};
