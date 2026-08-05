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

export type DemandStats = {
  consumer_leads: number;
  fr_leads: number;
  qualified_buyers: number;
  by_platform: Record<string, number>;
  by_status?: Record<string, number>;
  contact_found: number;
  contact_queued?: number;
  contact_contacted?: number;
  contact_engaged?: number;
};

export type ConsumerLead = {
  id: number;
  platform: string;
  handle: string;
  display_name: string | null;
  profile_url: string | null;
  language: string;
  country_hint: string | null;
  brands_interest: string[];
  buyer_score: number;
  lead_role: string;
  contact_status: string;
  contact_method: string | null;
  source_type: string;
  source_url: string | null;
  supplier_id: number | null;
  supplier_ref: string | null;
  snippet: string | null;
  first_seen_at: string;
  last_seen_at: string;
  seen_count: number;
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
      verify_thread_alive?: boolean;
      verify_running?: boolean;
      verify_phase?: string;
      verify_cycle?: number;
      verify_wa: boolean;
      parallel?: boolean;
      whatsapp?: number | null;
      wa_auth?: boolean;
      last_result?: { whatsapp_gained?: number; whatsapp_after?: number; wa_verify?: boolean } | null;
      last_verify_result?: {
        ok?: boolean;
        reachable?: number;
        dead?: number;
        checked?: number;
      } | null;
      last_error?: string | null;
    }>("/autopilot"),
  setAutopilot: (enabled: boolean, verify_wa = true) =>
    api<{ enabled: boolean; running: boolean; phase: string }>(
      `/autopilot?enabled=${enabled}&verify_wa=${verify_wa}`,
      { method: "POST" }
    ),
  demandStats: () => api<DemandStats>("/demand/stats"),
  consumers: (qs = "limit=50") => api<ConsumerLead[]>(`/consumers?${qs}`),
  consumersQueue: (limit = 50) => api<ConsumerLead[]>(`/consumers/queue?limit=${limit}`),
  enqueueConsumer: (id: number, note?: string) =>
    api<ConsumerLead>(
      `/consumers/${id}/enqueue${note ? `?note=${encodeURIComponent(note)}` : ""}`,
      { method: "POST" }
    ),
  patchConsumerContact: (id: number, status: string, note?: string) =>
    api<ConsumerLead>(`/consumers/${id}/contact`, {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    }),
  demandTick: () =>
    api<{ ok: boolean }>("/demand/tick", { method: "POST" }),
  demandHarvest: () =>
    api<{ ok: boolean }>("/demand/harvest", { method: "POST" }),
  demandEnrich: () =>
    api<{ ok: boolean }>("/demand/enrich", { method: "POST" }),
  demandAutopilot: () =>
    api<{
      enabled: boolean;
      running: boolean;
      phase: string;
      cycle: number;
      thread_alive: boolean;
      last_result?: { consumers_gained?: number; consumers_after?: number } | null;
      last_error?: string | null;
    }>("/demand/autopilot"),
  setDemandAutopilot: (enabled: boolean) =>
    api<{ enabled: boolean }>(`/demand/autopilot?enabled=${enabled}`, { method: "POST" }),
  consumersExportUrl: (fmt: "csv" | "json" = "csv") =>
    `${API}/consumers/export?fmt=${fmt}`,
  captureLead: (body: {
    email?: string;
    telegram?: string;
    brand_interest?: string;
    source?: string;
    message?: string;
  }) =>
    api<ConsumerLead>("/leads/capture", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  facadeConfig: () =>
    api<{ brand_name: string; telegram_url: string; tagline: string }>("/facade/config"),
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
