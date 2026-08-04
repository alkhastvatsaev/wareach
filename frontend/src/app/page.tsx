"use client";

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  Check,
  Copy,
  Download,
  ExternalLink,
  MessageCircle,
  Play,
  Plug,
  ShieldCheck,
  Square,
  X,
  Zap,
} from "lucide-react";
import { Contact, Stats, luxApi } from "@/lib/api";
import { BentoCell, BentoGrid } from "@/components/ui/bento-grid";
import LoadingState from "@/components/ui/loading-state";
import { AnimatedNumber } from "@/components/wareach/animated-number";
import { ProgressTrack } from "@/components/wareach/progress-track";
import { LiveDot } from "@/components/wareach/live-dot";
import { cn } from "@/lib/utils";

export default function Home() {
  const reduce = useReducedMotion();
  const [stats, setStats] = useState<Stats | null>(null);
  const [queue, setQueue] = useState<Contact[]>([]);
  const [running, setRunning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Prêt");
  const [error, setError] = useState<string | null>(null);
  const [idx, setIdx] = useState(0);
  const [waAuth, setWaAuth] = useState<boolean | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [autopilot, setAutopilot] = useState(false);
  const [autoPhase, setAutoPhase] = useState("idle");
  const [autoCycle, setAutoCycle] = useState(0);
  const [verifyPhase, setVerifyPhase] = useState("idle");
  const [verifyCycle, setVerifyCycle] = useState(0);
  const [connecting, setConnecting] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [s, q, ap] = await Promise.all([
        luxApi.stats(),
        luxApi.queue(),
        luxApi.autopilot().catch(() => null),
      ]);
      setStats(s);
      setQueue(q);
      setApiOk(true);
      if (ap) {
        setAutopilot(!!ap.enabled);
        setAutoPhase(ap.phase || "idle");
        setAutoCycle(ap.cycle || 0);
        setVerifyPhase(ap.verify_phase || "idle");
        setVerifyCycle(ap.verify_cycle || 0);
        if (typeof ap.wa_auth === "boolean") setWaAuth(ap.wa_auth);
      }
      setIdx((i) => (q.length ? Math.min(i, q.length - 1) : 0));
    } catch {
      setApiOk(false);
      setStats(null);
      setError(
        typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
          ? "API hors ligne — en cloud, définis BACKEND_URL (HTTPS) ou ouvre http://localhost:3000"
          : "API hors ligne — clique Connecter l’API"
      );
    }
  }, []);

  useEffect(() => {
    load();
    luxApi
      .verifyStatus()
      .then((s) => setWaAuth(s.auth_ready))
      .catch(() => setWaAuth(false));
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (!running) return;
    let cancelled = false;
    (async () => {
      while (!cancelled) {
        setBusy(true);
        setStatus("Recherche…");
        try {
          const res = await luxApi.runAuto();
          if (cancelled) break;
          const gained = res.result?.whatsapp_gained ?? 0;
          setStatus(gained > 0 ? `+${gained} contacts` : "Cycle OK");
          await load();
        } catch {
          if (!cancelled) setStatus("Erreur — retry");
        } finally {
          setBusy(false);
        }
        if (cancelled) break;
        setStatus("Pause…");
        await new Promise((r) => setTimeout(r, 20000));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [running, load]);

  const mark = useCallback(
    async (c: Contact, verifyStatus: string) => {
      await luxApi.verify(c.id, verifyStatus);
      await load();
    },
    [load]
  );

  const openAndCheck = useCallback(
    async (c: Contact) => {
      if (c.open_url) window.open(c.open_url, "_blank", "noopener,noreferrer");
      await luxApi.verify(c.id, "busy");
      await load();
    },
    [load]
  );

  const current = queue[idx] ?? null;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!current) return;
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      const k = e.key.toLowerCase();
      if (k === "o") {
        e.preventDefault();
        if (current.contact_type === "whatsapp" && current.open_url) openAndCheck(current);
        else if (current.contact_type === "wechat") {
          navigator.clipboard.writeText(current.normalized_value);
          mark(current, "busy");
        }
      } else if (k === "k" || k === "enter") {
        e.preventDefault();
        mark(current, "reachable");
      } else if (k === "m" || k === "backspace") {
        e.preventDefault();
        mark(current, "dead");
      } else if (k === "s" || k === "arrowdown") {
        e.preventDefault();
        setIdx((i) => Math.min(i + 1, Math.max(0, queue.length - 1)));
      } else if (k === "w" || k === "arrowup") {
        e.preventDefault();
        setIdx((i) => Math.max(0, i - 1));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [current, queue.length, mark, openAndCheck]);

  const offline = !stats;
  const wa = stats?.whatsapp ?? null;
  const wx = stats?.wechat ?? null;
  const target = stats?.whatsapp_target ?? 10000;
  const totalReach = wa != null && wx != null ? wa + wx : null;
  const pct = wa != null ? Math.min(100, Math.round((wa / target) * 100)) : 0;
  const unverified = stats?.unverified ?? null;
  const reachable = stats?.reachable ?? null;
  const dead = stats?.dead ?? null;
  const waPerH = stats?.wa_per_hour ?? 0;
  const eta = stats?.eta_hours_to_10k_wa;
  const waNew = stats?.wa_new_24h ?? null;
  const jobActive =
    busy || verifying || (autopilot && (autoPhase === "harvest" || verifyPhase === "verifying"));
  const loaderLabel = verifying
    ? "Vérification WhatsApp"
    : autopilot && verifyPhase === "verifying" && autoPhase !== "harvest"
      ? `WA verify #${verifyCycle}`
      : autopilot && autoPhase === "harvest"
        ? `Harvest #${autoCycle}${verifyPhase === "verifying" ? " + WA" : ""}`
        : busy
          ? status.replace(/…$/, "") || "Recherche"
          : running
            ? "Collecte en pause"
            : autopilot
              ? `Autopilote · ${autoPhase}/${verifyPhase}`
              : "Prêt";
  const loaderVariant =
    verifying || verifyPhase === "verifying"
      ? "Orbit"
      : busy || (autopilot && autoPhase === "harvest")
        ? "Drive"
        : "Dots";

  const connectApi = useCallback(async () => {
    setConnecting(true);
    setStatus("Connexion API…");
    try {
      const res = await luxApi.connectBackend();
      setStatus(res.message || (res.ok ? "API OK" : "Démarrage…"));
      for (let i = 0; i < 12; i++) {
        await new Promise((r) => setTimeout(r, 800));
        try {
          await luxApi.stats();
          await load();
          setError(null);
          setStatus("API reconnectée");
          return;
        } catch {
          /* keep polling */
        }
      }
      await load();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Échec connexion";
      setError(msg);
      setStatus(msg);
    } finally {
      setConnecting(false);
    }
  }, [load]);

  const toggleAutopilot = useCallback(async () => {
    try {
      const next = !autopilot;
      const res = await luxApi.setAutopilot(next, true);
      setAutopilot(!!res.enabled);
      setAutoPhase(res.phase || (next ? "harvest" : "paused"));
      setStatus(next ? "Autopilote ON" : "Autopilote OFF");
      await load();
    } catch {
      setStatus("Impossible de basculer l’autopilote");
    }
  }, [autopilot, load]);

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl px-5 pb-20 pt-8 md:px-8 md:pt-10">
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -left-24 top-24 h-64 w-64 rounded-full bg-[var(--accent)]/10 blur-3xl"
        animate={reduce ? undefined : { opacity: [0.35, 0.7, 0.35], y: [0, 18, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      <AnimatePresence>
        {(jobActive || running || autopilot) && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mb-6 flex items-center justify-between gap-4 rounded-2xl border border-[var(--accent)]/25 bg-[var(--ink)] px-4 py-3 text-[var(--surface)] shadow-panel"
            style={
              {
                ["--foreground" as string]: "#f7fafc",
                ["--muted-foreground" as string]: "rgba(247,250,252,0.55)",
              } as CSSProperties
            }
          >
            <LoadingState
              key={`${loaderLabel}-${jobActive}-${autoCycle}`}
              label={loaderLabel}
              variant={loaderVariant}
              active={jobActive || running || autopilot}
            />
            {(running || autopilot) && (
              <span className="hidden text-[11px] uppercase tracking-[0.16em] text-white/45 sm:inline">
                {autopilot ? "auto-pilote" : "cycle auto"}
              </span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.28em] text-[var(--accent)]">
            Brand protection OSINT
          </p>
          <h1 className="font-display text-4xl font-bold tracking-tight md:text-5xl">WAREACH</h1>
          <p className="mt-2 max-w-md text-sm text-[var(--muted)]">
            Collecte Chine · WhatsApp & WeChat · vérification live pour maisons LVMH / Richemont.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <LiveDot ok={apiOk} label={apiOk ? "API live" : apiOk === false ? "API down" : "API…"} />
          <LiveDot
            ok={waAuth}
            label={waAuth ? "WhatsApp session" : waAuth === false ? "WA offline" : "WA…"}
          />
          <LiveDot
            ok={autopilot ? true : apiOk === false ? false : null}
            label={
              autopilot
                ? `Auto · ${autoPhase} + WA ${verifyPhase}`
                : "Autopilote off"
            }
          />
          {apiOk === false && (
            <button
              type="button"
              disabled={connecting}
              onClick={connectApi}
              className="mt-1 inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-lg bg-[var(--accent)] px-3 text-xs font-semibold text-white transition hover:brightness-110 disabled:opacity-50"
            >
              <Plug className="h-3.5 w-3.5" />
              {connecting ? "Connexion…" : "Connecter l’API"}
            </button>
          )}
        </div>
      </header>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-[var(--warn)]"
        >
          <p>{error}</p>
          <button
            type="button"
            disabled={connecting}
            onClick={connectApi}
            className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-lg bg-[var(--ink)] px-3 text-xs font-semibold text-white"
          >
            <Plug className="h-3.5 w-3.5" />
            {connecting ? "Connexion…" : "Connecter l’API"}
          </button>
        </motion.div>
      )}

      <BentoGrid className="mb-8">
        <BentoCell span="md:col-span-4 md:row-span-2" className="min-h-[220px]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
            Reach total
          </p>
          <p className="mt-3 font-display text-6xl font-bold tracking-tight md:text-7xl">
            <AnimatedNumber value={totalReach} className="mono" />
          </p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            WA <span className="mono text-[var(--ink)]">{offline ? "—" : wa}</span>
            {" · "}
            WeChat <span className="mono text-[var(--ink)]">{offline ? "—" : wx}</span>
            {" · "}
            objectif {target.toLocaleString("fr-FR")}
          </p>
          <div className="mt-8 max-w-md">
            <ProgressTrack pct={pct} label="Progression WhatsApp → 10k" />
          </div>
          <p className="mt-4 text-xs text-[var(--muted)]">
            {offline
              ? "stats indisponibles"
              : waPerH > 0
                ? `${waPerH}/h WA · +${waNew ?? 0}/24h${eta != null ? ` · ETA ~${eta}h` : ""}`
                : `+${waNew ?? 0} WA / 24h · besoin ~${stats?.daily_pace_needed ?? 1429}/j`}
          </p>
          {stats?.top_alert && (
            <p className="mt-3 max-w-lg text-xs text-[var(--warn)]">{stats.top_alert}</p>
          )}
        </BentoCell>

        <BentoCell span="md:col-span-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Vérifiés OK
          </p>
          <p className="mt-3 font-display text-4xl font-semibold">
            <AnimatedNumber value={reachable} className="mono" />
          </p>
        </BentoCell>

        <BentoCell span="md:col-span-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            À vérifier
          </p>
          <p className="mt-3 font-display text-4xl font-semibold">
            <AnimatedNumber value={unverified} className="mono" />
          </p>
          <p className="mt-2 text-xs text-[var(--muted)]">
            morts <span className="mono text-[var(--ink)]">{offline ? "—" : dead}</span>
          </p>
        </BentoCell>

        <BentoCell span="md:col-span-3" className="!bg-[var(--ink)] text-[var(--surface)]">
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              disabled={apiOk === false}
              onClick={toggleAutopilot}
              className={cn(
                "inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl px-5 text-sm font-semibold transition duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:opacity-40",
                autopilot
                  ? "bg-[var(--surface)] text-[var(--ink)] hover:opacity-90"
                  : "bg-[var(--accent)] text-white hover:brightness-110"
              )}
            >
              <Zap className="h-4 w-4" />
              {autopilot ? "Stop autopilote" : "Autopilote"}
            </button>
            <button
              type="button"
              onClick={() => setRunning((v) => !v)}
              disabled={apiOk === false || autopilot}
              className={cn(
                "inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border border-white/20 px-5 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              )}
            >
              {running ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {running ? "Arrêter" : "1 cycle"}
            </button>
            <button
              type="button"
              disabled={verifying || waAuth === false || apiOk === false}
              onClick={async () => {
                setVerifying(true);
                setStatus("Vérif WhatsApp…");
                try {
                  const res = await luxApi.verifyBatch(25);
                  if (!res.ok) setStatus(String(res.result?.error || "Session WA manquante"));
                  else if (res.result?.started) setStatus("Vérif WA lancée (arrière-plan)");
                  else {
                    const imp = res.result?.import;
                    setStatus(`WA live: OK ${imp?.reachable ?? 0} · morts ${imp?.dead ?? 0}`);
                  }
                  await load();
                  const s = await luxApi.verifyStatus();
                  setWaAuth(s.auth_ready);
                } catch {
                  setStatus("Vérif échouée — ./scripts/whatsapp-login.sh");
                } finally {
                  setVerifying(false);
                }
              }}
              className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border border-white/20 px-5 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <ShieldCheck className="h-4 w-4" />
              {verifying ? "Vérification…" : "Vérifier WA"}
            </button>
            {apiOk === false && (
              <button
                type="button"
                disabled={connecting}
                onClick={connectApi}
                className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl bg-white px-5 text-sm font-semibold text-[var(--ink)]"
              >
                <Plug className="h-4 w-4" />
                Connecter l’API
              </button>
            )}
          </div>
          <p className="mt-4 min-h-5 text-xs text-white/65">
            {jobActive || running || autopilot ? (
              <span
                className="inline-block"
                style={
                  {
                    ["--foreground" as string]: "#f7fafc",
                    ["--muted-foreground" as string]: "rgba(247,250,252,0.55)",
                  } as CSSProperties
                }
              >
                <LoadingState
                  key={`panel-${loaderLabel}-${jobActive}-${autoCycle}`}
                  label={loaderLabel}
                  variant={loaderVariant}
                  active={jobActive || running || autopilot}
                />
              </span>
            ) : (
              status
            )}
            {waAuth === false && !jobActive && " · session absente — ./scripts/whatsapp-login.sh"}
          </p>
        </BentoCell>

        <BentoCell span="md:col-span-3">
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Exports
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={luxApi.exportUrl}
              className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border border-[var(--line)] bg-white/60 px-4 text-sm font-medium transition hover:border-[var(--accent)] hover:text-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
            >
              <Download className="h-4 w-4" />
              CSV WA + WeChat
            </a>
            <a
              href={luxApi.casePackUrl()}
              className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border border-[var(--line)] bg-white/60 px-4 text-sm font-medium transition hover:border-[var(--accent)] hover:text-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
            >
              <Download className="h-4 w-4" />
              Dossier juridique ZIP
            </a>
          </div>
        </BentoCell>
      </BentoGrid>

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface)]/85 p-5 shadow-panel backdrop-blur-sm md:p-7">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight">File de vérification</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              <kbd className="rounded bg-[var(--accent-soft)] px-1.5 py-0.5 font-mono text-[11px] text-[var(--accent)]">
                O
              </kbd>{" "}
              ouvrir ·{" "}
              <kbd className="rounded bg-[var(--accent-soft)] px-1.5 py-0.5 font-mono text-[11px] text-[var(--accent)]">
                K
              </kbd>{" "}
              OK ·{" "}
              <kbd className="rounded bg-[var(--accent-soft)] px-1.5 py-0.5 font-mono text-[11px] text-[var(--accent)]">
                M
              </kbd>{" "}
              mort ·{" "}
              <kbd className="rounded bg-[var(--accent-soft)] px-1.5 py-0.5 font-mono text-[11px] text-[var(--accent)]">
                S
              </kbd>{" "}
              suivant
            </p>
          </div>
          <p className="font-mono text-xs text-[var(--muted)]">{queue.length} en file</p>
        </div>

        <ul className="space-y-2">
          <AnimatePresence mode="popLayout">
            {queue.map((c, i) => {
              const active = i === idx;
              return (
                <motion.li
                  key={c.id}
                  layout
                  initial={reduce ? false : { opacity: 0, y: 10 }}
                  animate={{ opacity: active ? 1 : 0.55, y: 0 }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.25 }}
                  onClick={() => setIdx(i)}
                  className={cn(
                    "cursor-pointer rounded-xl border px-4 py-3 transition duration-200",
                    active
                      ? "border-[var(--accent)]/35 bg-[var(--accent-soft)]"
                      : "border-transparent hover:border-[var(--line)] hover:bg-white/50"
                  )}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-mono text-sm font-semibold tracking-tight">
                        {active ? "› " : ""}
                        {c.normalized_value}
                      </p>
                      <p className="mt-1 flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-[var(--muted)]">
                        <MessageCircle className="h-3 w-3" />
                        {c.contact_type}
                        {c.brand_context ? ` · ${c.brand_context}` : ""}
                      </p>
                    </div>
                    {active && (
                      <div className="flex flex-wrap gap-2">
                        {c.contact_type === "whatsapp" && c.open_url && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              openAndCheck(c);
                            }}
                            className="inline-flex min-h-10 cursor-pointer items-center gap-1.5 rounded-lg bg-[var(--accent)] px-3 text-xs font-semibold text-white transition hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            Ouvrir WhatsApp
                          </button>
                        )}
                        {c.contact_type === "wechat" && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigator.clipboard.writeText(c.normalized_value);
                              mark(c, "busy");
                            }}
                            className="inline-flex min-h-10 cursor-pointer items-center gap-1.5 rounded-lg border border-[var(--ink)] px-3 text-xs font-semibold transition hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
                          >
                            <Copy className="h-3.5 w-3.5" />
                            Copier WeChat
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            mark(c, "reachable");
                          }}
                          className="inline-flex min-h-10 cursor-pointer items-center gap-1 rounded-lg px-3 text-xs font-semibold text-[var(--accent)] transition hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
                        >
                          <Check className="h-3.5 w-3.5" />
                          OK
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            mark(c, "dead");
                          }}
                          className="inline-flex min-h-10 cursor-pointer items-center gap-1 rounded-lg px-3 text-xs font-medium text-[var(--muted)] transition hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
                        >
                          <X className="h-3.5 w-3.5" />
                          Mort
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIdx((v) => Math.max(0, v - 1));
                          }}
                          className="inline-flex min-h-10 w-10 cursor-pointer items-center justify-center rounded-lg text-[var(--muted)] hover:bg-white"
                          aria-label="Précédent"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIdx((v) => Math.min(v + 1, Math.max(0, queue.length - 1)));
                          }}
                          className="inline-flex min-h-10 w-10 cursor-pointer items-center justify-center rounded-lg text-[var(--muted)] hover:bg-white"
                          aria-label="Suivant"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
          {!queue.length && (
            <li className="rounded-xl border border-dashed border-[var(--line)] px-4 py-10 text-center text-sm text-[var(--muted)]">
              File vide — l’autopilote remplit la queue, ou lance un cycle manuel.
            </li>
          )}
        </ul>
      </section>
    </main>
  );
}
