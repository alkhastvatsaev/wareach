/**
 * Client API — always same-origin via Next proxy `/api/osint/*`
 * so HTTPS (Vercel) never hits http://127.0.0.1 (mixed content).
 * The proxy forwards to BACKEND_URL / local uvicorn.
 */

const API = "/api/osint";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const j = await res.json();
      if (j?.hint) detail = j.hint;
      else if (j?.error) detail = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export type Stats = {
  whatsapp: number;
  wechat: number;
  whatsapp_target: number;
  whatsapp_remaining: number;
  unverified: number;
  reachable: number;
  dead: number;
  wa_per_hour?: number;
  contacts_per_hour?: number;
  eta_hours_to_10k_wa?: number | null;
  wa_new_24h?: number;
  wx_new_24h?: number;
  daily_pace_needed?: number;
  top_alert?: string | null;
  alert_count?: number;
};

export type Contact = {
  id: number;
  contact_type: string;
  normalized_value: string;
  brand_context: string | null;
  source_url: string | null;
  verify_status: string;
  open_url: string | null;
};

export const luxApi = {
  stats: () => api<Stats>("/stats"),
  queue: () =>
    api<Contact[]>(
      "/contacts?contact_type=messageable&verify_status=unverified&limit=30"
    ),
  runAuto: () =>
    api<{ ok: boolean; result?: { whatsapp_after?: number; whatsapp_gained?: number } }>(
      "/jobs/auto?query_limit=18&dive_limit=6",
      { method: "POST" }
    ),
  verify: (id: number, status: string) =>
    api<{ ok: boolean }>(`/contacts/${id}/verify?status=${status}`, { method: "PATCH" }),
  verifyBatch: (limit = 30) =>
    api<{
      ok: boolean;
      result?: {
        started?: boolean;
        import?: { reachable?: number; dead?: number };
        error?: string;
        message?: string;
      };
    }>(`/jobs/whatsapp-verify?limit=${limit}&delay_ms=4000`, { method: "POST" }),
  verifyStatus: () =>
    api<{ auth_ready: boolean; login_hint: string }>("/whatsapp-verify/status"),
  exportUrl: `${API}/export/whatsapp-csv`,
  casePackUrl: (brand?: string) =>
    `${API}/export/case-pack${brand ? `?brand=${encodeURIComponent(brand)}` : ""}`,
  autopilot: () =>
    api<{
      enabled: boolean;
      running: boolean;
      phase: string;
      cycle: number;
      thread_alive: boolean;
      verify_wa: boolean;
      whatsapp?: number | null;
      wa_auth?: boolean;
      last_result?: { whatsapp_gained?: number; whatsapp_after?: number } | null;
      last_error?: string | null;
    }>("/autopilot"),
  setAutopilot: (enabled: boolean, verify_wa = true) =>
    api<{ enabled: boolean; running: boolean; phase: string }>(
      `/autopilot?enabled=${enabled}&verify_wa=${verify_wa}`,
      { method: "POST" }
    ),
  connectBackend: async () => {
    const res = await fetch("/api/backend/start", { method: "POST", cache: "no-store" });
    const data = (await res.json().catch(() => ({}))) as {
      ok?: boolean;
      message?: string;
      already_up?: boolean;
      error?: string;
      vercel?: boolean;
      hint?: string;
    };
    if (!res.ok || data.ok === false) {
      throw new Error(data.hint || data.error || data.message || `${res.status}`);
    }
    return data;
  },
};
