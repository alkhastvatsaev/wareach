"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { luxmatchApi } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFile = useCallback(
    async (file: File | null) => {
      if (!file || busy) return;
      if (!file.type.startsWith("image/")) {
        setError("Image uniquement (jpg, png, webp)");
        return;
      }
      setBusy(true);
      setError(null);
      try {
        const res = await luxmatchApi.analyze(file);
        sessionStorage.setItem(
          `luxmatch:${res.request_id}`,
          JSON.stringify({
            request_id: res.request_id,
            client_token: res.client_token,
            photo_url: res.photo_url,
            ai_description: res.ai_description,
          })
        );
        router.push(`/confirm/${res.request_id}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erreur analyse");
        setBusy(false);
      }
    },
    [busy, router]
  );

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center px-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(196,165,116,0.12),_transparent_60%)]" />
      <p className="mb-6 text-[11px] font-semibold uppercase tracking-[0.35em] text-[var(--accent)]">
        LuxMatch
      </p>
      <h1 className="font-display mb-3 text-center text-4xl font-semibold tracking-tight md:text-5xl">
        Déposez une photo
      </h1>
      <p className="mb-10 max-w-sm text-center text-sm text-[var(--muted)]">
        On décrit l’article, on demande des devis à des vendeurs, vous choisissez.
      </p>

      <label
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          onFile(e.dataTransfer.files?.[0] || null);
        }}
        className={`relative flex h-56 w-full max-w-md cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed transition ${
          dragging
            ? "border-[var(--accent)] bg-[var(--accent)]/10"
            : "border-white/20 bg-white/[0.03] hover:border-white/35"
        } ${busy ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          type="file"
          accept="image/*"
          className="absolute inset-0 cursor-pointer opacity-0"
          disabled={busy}
          onChange={(e) => onFile(e.target.files?.[0] || null)}
        />
        <span className="text-sm text-white/70">
          {busy ? "Analyse en cours…" : "Glisser une image ou cliquer"}
        </span>
        <span className="mt-2 text-[11px] text-white/35">JPG · PNG · WEBP</span>
      </label>

      {error && <p className="mt-6 text-sm text-rose-300">{error}</p>}
    </main>
  );
}
