"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AiDescription, luxmatchApi } from "@/lib/api";

type Stored = {
  request_id: number;
  client_token: string;
  photo_url: string;
  ai_description: AiDescription;
};

export default function ConfirmPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [data, setData] = useState<Stored | null>(null);
  const [edit, setEdit] = useState("");
  const [email, setEmail] = useState("");
  const [telegram, setTelegram] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(`luxmatch:${id}`);
    if (!raw) {
      setError("Session expirée — déposez à nouveau une photo.");
      return;
    }
    const parsed = JSON.parse(raw) as Stored;
    setData(parsed);
    const ai = parsed.ai_description || {};
    const draft = [ai.brand, ai.model, ai.color, ai.summary].filter(Boolean).join(" — ");
    setEdit(draft);
  }, [id]);

  async function confirm() {
    if (!data) return;
    setBusy(true);
    setError(null);
    try {
      const res = await luxmatchApi.confirm({
        request_id: data.request_id,
        user_edit: edit,
        contact_email: email || undefined,
        contact_telegram: telegram || undefined,
      });
      router.push(`/r/${res.client_token}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
      setBusy(false);
    }
  }

  if (!data && !error) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-white/50">Chargement…</main>;
  }

  const photo = data ? luxmatchApi.photoUrl(data.photo_url) : "";

  return (
    <main className="mx-auto min-h-screen max-w-lg px-5 py-12">
      <p className="text-[11px] uppercase tracking-[0.3em] text-[var(--accent)]">LuxMatch · Étape 1</p>
      <h1 className="font-display mt-3 text-3xl font-semibold">C’est bien ça ?</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">Corrigez la description si besoin, puis confirmez.</p>

      {photo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photo} alt="Produit" className="mt-8 max-h-64 w-full rounded-2xl object-contain bg-black/40" />
      )}

      {data?.ai_description?.mock && (
        <p className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          IA en mode démo (pas de clé OpenAI). Décrivez le produit précisément ci-dessous.
        </p>
      )}

      <label className="mt-6 block text-xs uppercase tracking-wide text-white/40">Description</label>
      <textarea
        value={edit}
        onChange={(e) => setEdit(e.target.value)}
        rows={5}
        className="mt-2 w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
      />

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <input
          type="email"
          placeholder="Email (optionnel)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
        />
        <input
          type="text"
          placeholder="@telegram (optionnel)"
          value={telegram}
          onChange={(e) => setTelegram(e.target.value)}
          className="rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
        />
      </div>

      {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

      <button
        type="button"
        disabled={busy || !edit.trim()}
        onClick={confirm}
        className="mt-8 w-full rounded-full bg-[var(--accent)] py-3.5 text-sm font-semibold text-[#0a0908] disabled:opacity-50"
      >
        {busy ? "Envoi aux vendeurs…" : "Oui, je cherche ça — recevoir des devis"}
      </button>
    </main>
  );
}
