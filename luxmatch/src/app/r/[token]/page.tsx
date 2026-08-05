"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { luxmatchApi } from "@/lib/api";

type Quote = {
  id: number;
  price: number;
  currency: string;
  description?: string;
  shipping?: string;
  payment_methods?: string[];
  status: string;
};

export default function ClientRfqPage() {
  const params = useParams();
  const token = String(params.token || "");
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const v = await luxmatchApi.client(token);
      setData(v);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    }
  }, [token]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  async function select(quoteId: number) {
    setBusy(true);
    try {
      await luxmatchApi.select(token, quoteId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  async function review() {
    setBusy(true);
    try {
      await luxmatchApi.review(token, rating, comment);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  if (!data && !error) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-white/50">Chargement…</main>;
  }

  const quotes = (data?.quotes as Quote[]) || [];
  const status = String(data?.status || "");
  const photo = luxmatchApi.photoUrl(String(data?.photo_url || ""));
  const sent = Number(data?.sent_count || 0);
  const product = String(data?.user_edit || (data?.ai_description as { summary?: string })?.summary || "");

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-5 py-12">
      <p className="text-[11px] uppercase tracking-[0.3em] text-[var(--accent)]">LuxMatch · Vos devis</p>
      <h1 className="font-display mt-3 text-3xl font-semibold">Demandes en cours</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        Statut : <span className="text-white/80">{status}</span> · Messages envoyés : {sent}/10 · Devis :{" "}
        {quotes.length}
      </p>

      {photo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photo} alt="" className="mt-6 max-h-40 rounded-xl object-contain bg-black/30" />
      )}
      {product && <p className="mt-4 text-sm text-white/70">{product}</p>}
      {data?.blast_error ? (
        <p className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          WhatsApp : {String(data.blast_error)}
        </p>
      ) : null}

      <section className="mt-10 space-y-3">
        <h2 className="font-display text-xl">Devis reçus</h2>
        {quotes.length === 0 ? (
          <p className="text-sm text-white/45">En attente des vendeurs… cette page se met à jour seule.</p>
        ) : (
          quotes.map((q) => (
            <div key={q.id} className="rounded-2xl border border-white/12 bg-white/[0.03] p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-display text-2xl">
                  {q.price} {q.currency}
                </p>
                <span className="text-[11px] uppercase text-white/40">{q.status}</span>
              </div>
              {q.description && <p className="mt-2 text-sm text-white/65">{q.description}</p>}
              {q.shipping && <p className="mt-1 text-xs text-white/45">Expédition : {q.shipping}</p>}
              {q.payment_methods?.length ? (
                <p className="mt-1 text-xs text-white/45">Paiement : {q.payment_methods.join(", ")}</p>
              ) : null}
              {status !== "selected" && status !== "completed" && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => select(q.id)}
                  className="mt-4 rounded-full bg-[var(--accent)] px-4 py-2 text-xs font-semibold text-[#0a0908]"
                >
                  Choisir ce devis
                </button>
              )}
            </div>
          ))
        )}
      </section>

      {(status === "selected" || status === "completed") && (
        <section className="mt-10 rounded-2xl border border-white/12 p-5">
          <h2 className="font-display text-xl">Laisser un avis</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">Après votre commande — notez le vendeur.</p>
          <div className="mt-4 flex gap-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setRating(n)}
                className={`h-10 w-10 rounded-full border text-sm ${
                  rating >= n ? "border-[var(--accent)] bg-[var(--accent)]/20" : "border-white/15"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            placeholder="Commentaire (optionnel)"
            className="mt-4 w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm"
          />
          <button
            type="button"
            disabled={busy || status === "completed"}
            onClick={review}
            className="mt-4 rounded-full border border-white/20 px-4 py-2 text-xs font-semibold disabled:opacity-50"
          >
            {status === "completed" ? "Avis enregistré" : "Envoyer l’avis"}
          </button>
        </section>
      )}

      {error && <p className="mt-6 text-sm text-rose-300">{error}</p>}
    </main>
  );
}
