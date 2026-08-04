const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status}`);
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
  stats: () => api<Stats>("/api/stats"),
  queue: () =>
    api<Contact[]>(
      "/api/contacts?contact_type=messageable&verify_status=unverified&limit=30"
    ),
  runAuto: () =>
    api<{ ok: boolean; result?: { whatsapp_after?: number; whatsapp_gained?: number } }>(
      "/api/jobs/auto?query_limit=18&dive_limit=6",
      { method: "POST" }
    ),
  verify: (id: number, status: string) =>
    api<{ ok: boolean }>(`/api/contacts/${id}/verify?status=${status}`, { method: "PATCH" }),
  verifyBatch: (limit = 30) =>
    api<{
      ok: boolean;
      result?: {
        started?: boolean;
        import?: { reachable?: number; dead?: number };
        error?: string;
        message?: string;
      };
    }>(`/api/jobs/whatsapp-verify?limit=${limit}&delay_ms=4000`, { method: "POST" }),
  verifyStatus: () =>
    api<{ auth_ready: boolean; login_hint: string }>("/api/whatsapp-verify/status"),
  exportUrl: `${API}/api/export/whatsapp-csv`,
  casePackUrl: (brand?: string) =>
    `${API}/api/export/case-pack${brand ? `?brand=${encodeURIComponent(brand)}` : ""}`,
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
    }>("/api/autopilot"),
  setAutopilot: (enabled: boolean, verify_wa = true) =>
    api<{ enabled: boolean; running: boolean; phase: string }>(
      `/api/autopilot?enabled=${enabled}&verify_wa=${verify_wa}`,
      { method: "POST" }
    ),
  connectBackend: async () => {
    const res = await fetch("/api/backend/start", { method: "POST", cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json() as Promise<{ ok: boolean; message?: string; already_up?: boolean }>;
  },
};
