"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  Download,
  Play,
  Plug,
  Square,
  UserPlus,
  MessageSquare,
  Zap,
} from "lucide-react";
import { ConsumerLead, DemandStats, luxApi } from "@/lib/api";
import { BentoCell, BentoGrid } from "@/components/ui/bento-grid";
import Velaris from "@/components/ui/velaris";
import { AnimatedNumber } from "@/components/wareach/animated-number";
import { LiveDot } from "@/components/wareach/live-dot";
import { OpsNav } from "@/components/wareach/ops-nav";
import { cn } from "@/lib/utils";

export default function DemandPage() {
  const [stats, setStats] = useState<DemandStats | null>(null);
  const [leads, setLeads] = useState<ConsumerLead[]>([]);
  const [queue, setQueue] = useState<ConsumerLead[]>([]);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [autopilot, setAutopilot] = useState(false);
  const [autoPhase, setAutoPhase] = useState("idle");
  const [autoCycle, setAutoCycle] = useState(0);
  const [platform, setPlatform] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Prêt");
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const qs = new URLSearchParams({ limit: "80" });
      if (platform) qs.set("platform", platform);
      const [s, c, q, ap] = await Promise.all([
        luxApi.demandStats(),
        luxApi.consumers(qs.toString()),
        luxApi.consumersQueue(40),
        luxApi.demandAutopilot().catch(() => null),
      ]);
      setStats(s);
      let list = c;
      if (statusFilter) list = list.filter((l) => l.contact_status === statusFilter);
      setLeads(list);
      setQueue(q);
      setApiOk(true);
      if (ap) {
        setAutopilot(!!ap.enabled);
        setAutoPhase(ap.phase || "idle");
        setAutoCycle(ap.cycle || 0);
      }
    } catch {
      setApiOk(false);
      setStats(null);
      setError("API hors ligne — Connecter l’API");
    }
  }, [platform, statusFilter]);

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  async function connectApi() {
    setConnecting(true);
    try {
      await luxApi.connectBackend();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connexion échouée");
    } finally {
      setConnecting(false);
    }
  }

  async function toggleAuto() {
    setBusy(true);
    try {
      await luxApi.setDemandAutopilot(!autopilot);
      setStatus(!autopilot ? "Demand autopilot ON" : "Demand autopilot OFF");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur autopilot");
    } finally {
      setBusy(false);
    }
  }

  async function runTick() {
    setBusy(true);
    setStatus("Cycle demand…");
    try {
      await luxApi.demandTick();
      setStatus("Cycle lancé");
      setTimeout(load, 4000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tick failed");
    } finally {
      setBusy(false);
    }
  }

  async function runHarvest() {
    setBusy(true);
    setStatus("Harvest plateformes…");
    try {
      await luxApi.demandHarvest();
      setStatus("Harvest lancé");
      setTimeout(load, 5000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Harvest failed");
    } finally {
      setBusy(false);
    }
  }

  async function enqueue(id: number) {
    try {
      await luxApi.enqueueConsumer(id);
      setStatus(`Lead #${id} → queue`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Enqueue failed");
    }
  }

  async function markContacted(id: number) {
    try {
      await luxApi.patchConsumerContact(id, "contacted");
      setStatus(`Lead #${id} contacted`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    }
  }

  const platforms = useMemo(() => Object.keys(stats?.by_platform || {}), [stats]);
  const total = stats?.consumer_leads ?? 0;
  const fr = stats?.fr_leads ?? 0;
  const buyers = stats?.qualified_buyers ?? 0;
  const queued = stats?.contact_queued ?? 0;

  return (
    <Velaris
      height="100%"
      className="min-h-screen"
      bg="#071016"
      colors={["#5eead4", "#0d7377", "#134e4a", "#0c1419"]}
      speed={1.2}
      grain={0.2}
    >
      <main
        className="relative mx-auto min-h-screen max-w-6xl px-5 pb-20 pt-8 text-white md:px-8 md:pt-10"
        style={
          {
            ["--ink" as string]: "#f3faf9",
            ["--muted" as string]: "rgba(243,250,249,0.62)",
            ["--line" as string]: "rgba(255,255,255,0.14)",
            ["--border" as string]: "rgba(255,255,255,0.12)",
            ["--surface" as string]: "rgba(7,16,22,0.55)",
            ["--accent-soft" as string]: "rgba(13,115,119,0.28)",
          } as CSSProperties
        }
      >
        <OpsNav />

        <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.28em] text-teal-300/90">
              Phase 2 · DemandReach
            </p>
            <h1 className="font-display text-4xl font-bold tracking-tight md:text-5xl">Consumers FR</h1>
            <p className="mt-2 max-w-md text-sm text-white/65">
              Find · Enrich · Queue · Reach — Reddit, YouTube, Telegram, Discord, web.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 text-white/70">
            <LiveDot ok={apiOk} label={apiOk ? "API live" : apiOk === false ? "API down" : "API…"} />
            <LiveDot
              ok={autopilot ? true : apiOk === false ? false : null}
              label={autopilot ? `Demand · ${autoPhase} #${autoCycle}` : "Demand autopilot off"}
            />
            {apiOk === false && (
              <button
                type="button"
                disabled={connecting}
                onClick={connectApi}
                className="mt-1 inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--accent)] px-3 text-xs font-semibold text-white"
              >
                <Plug className="h-3.5 w-3.5" />
                {connecting ? "Connexion…" : "Connecter l’API"}
              </button>
            )}
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        <BentoGrid className="mb-8">
          <BentoCell span="md:col-span-3" className="min-h-[140px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Leads</p>
            <p className="mt-2 font-display text-5xl font-bold">
              <AnimatedNumber value={total} className="mono" />
            </p>
          </BentoCell>
          <BentoCell span="md:col-span-3" className="min-h-[140px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">FR</p>
            <p className="mt-2 font-display text-5xl font-bold">
              <AnimatedNumber value={fr} className="mono" />
            </p>
          </BentoCell>
          <BentoCell span="md:col-span-3" className="min-h-[140px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Buyers</p>
            <p className="mt-2 font-display text-5xl font-bold">
              <AnimatedNumber value={buyers} className="mono" />
            </p>
          </BentoCell>
          <BentoCell span="md:col-span-3" className="min-h-[140px]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Queue</p>
            <p className="mt-2 font-display text-5xl font-bold">
              <AnimatedNumber value={queued} className="mono" />
            </p>
          </BentoCell>
        </BentoGrid>

        <div className="mb-8 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={toggleAuto}
            className={cn(
              "inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-xs font-semibold",
              autopilot ? "bg-rose-500/80 text-white" : "bg-[var(--accent)] text-white"
            )}
          >
            {autopilot ? <Square className="h-3.5 w-3.5" /> : <Zap className="h-3.5 w-3.5" />}
            {autopilot ? "Stop demand" : "Start demand"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={runTick}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/20 bg-white/5 px-3 text-xs font-semibold text-white"
          >
            <Play className="h-3.5 w-3.5" />
            Tick
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={runHarvest}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/20 bg-white/5 px-3 text-xs font-semibold text-white"
          >
            Harvest YT/TG/DC
          </button>
          <a
            href={luxApi.consumersExportUrl("csv")}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/20 bg-white/5 px-3 text-xs font-semibold text-white"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </a>
          <span className="self-center text-[11px] text-white/40">{status}</span>
        </div>

        {stats?.by_platform && Object.keys(stats.by_platform).length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {Object.entries(stats.by_platform).map(([p, n]) => (
              <button
                key={p}
                type="button"
                onClick={() => setPlatform(platform === p ? "" : p)}
                className={cn(
                  "rounded-full border px-3 py-1 text-[11px] font-medium uppercase tracking-wide",
                  platform === p
                    ? "border-teal-400/50 bg-teal-400/15 text-teal-200"
                    : "border-white/15 text-white/50 hover:text-white/80"
                )}
              >
                {p} · {n}
              </button>
            ))}
            {platforms.length > 0 && platform && (
              <button
                type="button"
                onClick={() => setPlatform("")}
                className="rounded-full border border-white/10 px-3 py-1 text-[11px] text-white/40"
              >
                clear
              </button>
            )}
          </div>
        )}

        <div className="mb-4 flex flex-wrap gap-2">
          {["", "found", "queued", "contacted", "engaged"].map((s) => (
            <button
              key={s || "all"}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={cn(
                "rounded-full border px-3 py-1 text-[11px] uppercase tracking-wide",
                statusFilter === s
                  ? "border-teal-400/50 bg-teal-400/15 text-teal-200"
                  : "border-white/15 text-white/45"
              )}
            >
              {s || "all"}
            </button>
          ))}
        </div>

        <section className="mb-10">
          <h2 className="mb-3 font-display text-lg font-semibold">Queue contact</h2>
          {queue.length === 0 ? (
            <p className="text-sm text-white/45">Aucun lead en queue — enrichissez ou enqueuez manuellement.</p>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-white/12">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="border-b border-white/10 text-[11px] uppercase tracking-wide text-white/40">
                  <tr>
                    <th className="px-3 py-2">Handle</th>
                    <th className="px-3 py-2">Platform</th>
                    <th className="px-3 py-2">Score</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map((l) => (
                    <tr key={l.id} className="border-b border-white/5">
                      <td className="px-3 py-2">
                        <a
                          href={l.profile_url || l.source_url || "#"}
                          target="_blank"
                          rel="noreferrer"
                          className="text-teal-200 hover:underline"
                        >
                          {l.handle}
                        </a>
                      </td>
                      <td className="px-3 py-2 text-white/55">{l.platform}</td>
                      <td className="mono px-3 py-2">{Math.round(l.buyer_score)}</td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => markContacted(l.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-white/15 px-2 py-1 text-[11px] hover:bg-white/10"
                        >
                          <MessageSquare className="h-3 w-3" />
                          Contacted
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-3 font-display text-lg font-semibold">Tous les leads</h2>
          <div className="overflow-x-auto rounded-2xl border border-white/12">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-white/10 text-[11px] uppercase tracking-wide text-white/40">
                <tr>
                  <th className="px-3 py-2">Handle</th>
                  <th className="px-3 py-2">Platform</th>
                  <th className="px-3 py-2">Role</th>
                  <th className="px-3 py-2">FR</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((l) => (
                  <tr key={l.id} className="border-b border-white/5 align-top">
                    <td className="px-3 py-2">
                      <div className="font-medium">{l.display_name || l.handle}</div>
                      {l.snippet && (
                        <p className="mt-1 max-w-xs truncate text-[11px] text-white/40">{l.snippet}</p>
                      )}
                    </td>
                    <td className="px-3 py-2 text-white/55">{l.platform}</td>
                    <td className="px-3 py-2 text-white/55">{l.lead_role}</td>
                    <td className="px-3 py-2">{l.country_hint || "—"}</td>
                    <td className="mono px-3 py-2">{Math.round(l.buyer_score)}</td>
                    <td className="px-3 py-2 text-white/55">{l.contact_status}</td>
                    <td className="px-3 py-2">
                      {l.contact_status === "found" && (
                        <button
                          type="button"
                          onClick={() => enqueue(l.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-white/15 px-2 py-1 text-[11px] hover:bg-white/10"
                        >
                          <UserPlus className="h-3 w-3" />
                          Queue
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {leads.length === 0 && (
              <p className="px-4 py-8 text-center text-sm text-white/40">Aucun lead — lancez un tick ou harvest.</p>
            )}
          </div>
        </section>
      </main>
    </Velaris>
  );
}
