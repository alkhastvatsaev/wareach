"use client";

import { FormEvent, useState } from "react";
import { luxApi } from "@/lib/api";

type Props = {
  brandInterest?: string;
  telegramUrl?: string;
};

export function CaptureForm({ brandInterest, telegramUrl }: Props) {
  const [email, setEmail] = useState("");
  const [telegram, setTelegram] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "err">("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setError(null);
    try {
      await luxApi.captureLead({
        email: email || undefined,
        telegram: telegram || undefined,
        brand_interest: brandInterest,
        source: "facade",
        message: message || undefined,
      });
      setStatus("ok");
      setEmail("");
      setTelegram("");
      setMessage("");
    } catch (err) {
      setStatus("err");
      setError(err instanceof Error ? err.message : "Erreur");
    }
  }

  if (status === "ok") {
    return (
      <div className="rounded-2xl border border-teal-400/30 bg-teal-400/10 p-6 text-center">
        <p className="font-display text-xl text-white">Bienvenue</p>
        <p className="mt-2 text-sm text-white/65">
          Nous vous recontactons discrètement.{" "}
          {telegramUrl && (
            <a href={telegramUrl} className="text-teal-300 underline underline-offset-2" target="_blank" rel="noreferrer">
              Rejoindre Telegram
            </a>
          )}
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-white/12 bg-black/35 p-6 backdrop-blur-md">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-300/90">Accès guide</p>
      <p className="text-sm text-white/60">Email ou Telegram — au choix.</p>
      <input
        type="email"
        placeholder="email@exemple.fr"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/35 outline-none focus:border-teal-400/50"
      />
      <input
        type="text"
        placeholder="@telegram"
        value={telegram}
        onChange={(e) => setTelegram(e.target.value)}
        className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/35 outline-none focus:border-teal-400/50"
      />
      <textarea
        placeholder="Marque ou question (optionnel)"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        rows={3}
        className="w-full resize-none rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/35 outline-none focus:border-teal-400/50"
      />
      {error && <p className="text-sm text-rose-300">{error}</p>}
      <button
        type="submit"
        disabled={status === "loading" || (!email && !telegram)}
        className="w-full rounded-xl bg-[var(--accent)] py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-50"
      >
        {status === "loading" ? "Envoi…" : "Recevoir le guide"}
      </button>
    </form>
  );
}
