"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { luxmatchApi } from "@/lib/api";

const PAYMENTS = ["PayPal", "Carte bancaire", "Apple Pay", "Virement", "Western Union", "Autre"];

export default function SupplierFormPage() {
  const params = useParams();
  const token = String(params.token || "");
  const [product, setProduct] = useState("");
  const [photo, setPhoto] = useState("");
  const [already, setAlready] = useState(false);
  const [price, setPrice] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [description, setDescription] = useState("");
  const [shipping, setShipping] = useState("");
  const [methods, setMethods] = useState<string[]>([]);
  const [ok, setOk] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    luxmatchApi
      .supplier(token)
      .then((v) => {
        setProduct(String(v.product || ""));
        setPhoto(luxmatchApi.photoUrl(String(v.photo_url || "")));
        setAlready(Boolean(v.already_quoted));
        const q = v.quote as Record<string, unknown> | null;
        if (q) {
          setPrice(String(q.price ?? ""));
          setCurrency(String(q.currency || "USD"));
          setDescription(String(q.description || ""));
          setShipping(String(q.shipping || ""));
          setMethods((q.payment_methods as string[]) || []);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Lien invalide"));
  }, [token]);

  function toggle(m: string) {
    setMethods((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await luxmatchApi.quote(token, {
        price: Number(price),
        currency,
        description,
        shipping,
        payment_methods: methods,
      });
      setOk(true);
      setAlready(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  if (ok) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-5 text-center">
        <p className="font-display text-3xl">Devis envoyé</p>
        <p className="mt-3 text-sm text-[var(--muted)]">Le client verra votre offre sur LuxMatch.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-md px-5 py-10">
      <p className="text-[11px] uppercase tracking-[0.3em] text-[var(--accent)]">LuxMatch · Vendeur</p>
      <h1 className="font-display mt-3 text-3xl font-semibold">Votre devis</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">{product || "Demande client"}</p>
      {photo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photo} alt="" className="mt-6 max-h-48 w-full rounded-xl object-contain bg-black/30" />
      )}
      {already && (
        <p className="mt-4 text-xs text-amber-200/80">Vous avez déjà proposé un devis — vous pouvez le mettre à jour.</p>
      )}

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <div className="flex gap-2">
          <input
            required
            type="number"
            step="0.01"
            min="0"
            placeholder="Prix"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="flex-1 rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm"
          />
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="rounded-xl border border-white/15 bg-[#0a0908] px-3 text-sm"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="CNY">CNY</option>
          </select>
        </div>
        <textarea
          placeholder="Description / batch / qualité"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm"
        />
        <input
          placeholder="Expédition (délai, ligne, pays)"
          value={shipping}
          onChange={(e) => setShipping(e.target.value)}
          className="w-full rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm"
        />
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-white/40">Paiement accepté</p>
          <div className="flex flex-wrap gap-2">
            {PAYMENTS.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => toggle(m)}
                className={`rounded-full border px-3 py-1.5 text-xs ${
                  methods.includes(m) ? "border-[var(--accent)] bg-[var(--accent)]/20" : "border-white/15"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
        {error && <p className="text-sm text-rose-300">{error}</p>}
        <button
          type="submit"
          disabled={busy || !price}
          className="w-full rounded-full bg-[var(--accent)] py-3.5 text-sm font-semibold text-[#0a0908] disabled:opacity-50"
        >
          {busy ? "Envoi…" : "Envoyer le devis"}
        </button>
      </form>
    </main>
  );
}
