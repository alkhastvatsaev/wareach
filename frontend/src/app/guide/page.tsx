import type { Metadata } from "next";
import Link from "next/link";
import { CaptureForm } from "@/components/luxfind/capture-form";
import { BRAND_GUIDES } from "@/lib/luxfind-brands";

export const metadata: Metadata = {
  title: "LuxFind FR — Guide discret pour acheteurs exigeants",
  description:
    "Guide premium discret pour acheteurs français : vendeurs, QC, livraison. Louis Vuitton, Hermès, Chanel, Dior…",
};

const TELEGRAM = process.env.NEXT_PUBLIC_FACADE_TELEGRAM_URL || "https://t.me/luxfindfr";
const TAGLINE = process.env.NEXT_PUBLIC_FACADE_TAGLINE || "Guide discret pour acheteurs exigeants";

export default function GuidePage() {
  return (
    <div className="min-h-screen bg-[#060b10] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(13,115,119,0.18),_transparent_55%)]" />
      <main className="relative mx-auto max-w-5xl px-5 py-14 md:px-8 md:py-20">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.32em] text-teal-300/90">
          LuxFind FR
        </p>
        <h1 className="font-display max-w-2xl text-4xl font-bold tracking-tight md:text-6xl">
          {TAGLINE}
        </h1>
        <p className="mt-5 max-w-xl text-base leading-relaxed text-white/65 md:text-lg">
          Un espace calme pour les acheteurs français qui veulent des repères fiables :
          vendeurs, QC, agents, livraison — sans le bruit des forums.
        </p>

        <div className="mt-10 flex flex-wrap gap-3">
          <a
            href={TELEGRAM}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-full bg-[var(--accent)] px-5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            Canal Telegram
          </a>
          <a
            href="#acces"
            className="inline-flex min-h-11 items-center rounded-full border border-white/20 px-5 text-sm font-medium text-white/80 transition hover:border-white/40"
          >
            Accès email
          </a>
        </div>

        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Guides par maison</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {BRAND_GUIDES.map((b) => (
              <Link
                key={b.slug}
                href={`/guide/${b.slug}`}
                className="rounded-2xl border border-white/12 bg-white/[0.03] p-5 transition hover:border-teal-400/35 hover:bg-teal-400/5"
              >
                <p className="text-[11px] uppercase tracking-[0.18em] text-white/40">Guide</p>
                <p className="mt-2 font-display text-xl font-semibold">{b.name}</p>
                <p className="mt-2 line-clamp-2 text-sm text-white/55">{b.intro}</p>
              </Link>
            ))}
          </div>
        </section>

        <section id="acces" className="mt-16 grid gap-8 md:grid-cols-2 md:items-start">
          <div>
            <h2 className="font-display text-2xl font-semibold">Recevoir le guide</h2>
            <p className="mt-3 text-sm leading-relaxed text-white/60">
              Laissez un contact. Pas de newsletter agressive — uniquement l’accès au guide
              et les mises à jour utiles.
            </p>
            <ul className="mt-6 space-y-2 text-sm text-white/55">
              <li>— Checklists QC par marque</li>
              <li>— Signaux vendeurs à éviter</li>
              <li>— Tips livraison France</li>
            </ul>
          </div>
          <CaptureForm telegramUrl={TELEGRAM} />
        </section>

        <footer className="mt-20 border-t border-white/10 pt-6 text-xs text-white/35">
          LuxFind FR — entité indépendante. Contenu informatif à destination d’adultes.
        </footer>
      </main>
    </div>
  );
}
