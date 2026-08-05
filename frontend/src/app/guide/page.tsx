import type { Metadata } from "next";
import Link from "next/link";
import { CaptureForm } from "@/components/luxfind/capture-form";
import { TelegramSticky } from "@/components/luxfind/telegram-sticky";
import { pagesByIntent } from "@/lib/luxfind-pages";

export const metadata: Metadata = {
  title: "LuxFind FR — Guide discret pour acheteurs exigeants",
  description:
    "Guides pratiques France : Yupoo, agents, QC, douane, maisons. Contact Telegram ou email.",
  alternates: {
    canonical: `${process.env.NEXT_PUBLIC_SITE_URL || "https://wareach.vercel.app"}/guide`,
  },
};

const TELEGRAM = process.env.NEXT_PUBLIC_FACADE_TELEGRAM_URL || "https://t.me/luxfindfr";
const TAGLINE = process.env.NEXT_PUBLIC_FACADE_TAGLINE || "Guide discret pour acheteurs exigeants";

function CardGrid({
  items,
}: {
  items: { slug: string; title: string; blurb: string; label: string }[];
}) {
  return (
    <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((b) => (
        <Link
          key={b.slug}
          href={`/guide/${b.slug}`}
          className="rounded-2xl border border-white/12 bg-white/[0.03] p-5 transition hover:border-teal-400/35 hover:bg-teal-400/5"
        >
          <p className="text-[11px] uppercase tracking-[0.18em] text-white/40">{b.label}</p>
          <p className="mt-2 font-display text-lg font-semibold leading-snug">{b.title}</p>
          <p className="mt-2 line-clamp-2 text-sm text-white/55">{b.blurb}</p>
        </Link>
      ))}
    </div>
  );
}

export default function GuidePage() {
  const buy = pagesByIntent("buy");
  const howto = pagesByIntent("howto");
  const brands = pagesByIntent("brand");
  const models = pagesByIntent("model");

  return (
    <div className="min-h-screen bg-[#060b10] pb-24 text-white md:pb-0">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(13,115,119,0.18),_transparent_55%)]" />
      <main className="relative mx-auto max-w-5xl px-5 py-14 md:px-8 md:py-20">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.32em] text-teal-300/90">
          LuxFind FR
        </p>
        <h1 className="font-display max-w-2xl text-4xl font-bold tracking-tight md:text-6xl">
          {TAGLINE}
        </h1>
        <p className="mt-5 max-w-xl text-base leading-relaxed text-white/65 md:text-lg">
          Des guides clairs pour acheteurs français : Yupoo, WhatsApp vendeur, agents, QC,
          douane, livraison — et un contact direct quand vous êtes prêt.
        </p>

        <div className="mt-10 flex flex-wrap gap-3">
          <a
            href={TELEGRAM}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-full bg-[var(--accent)] px-5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            Contacter sur Telegram
          </a>
          <a
            href="#acces"
            className="inline-flex min-h-11 items-center rounded-full border border-white/20 px-5 text-sm font-medium text-white/80 transition hover:border-white/40"
          >
            Laisser un email
          </a>
        </div>

        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Acheter / trouver</h2>
          <p className="mt-2 text-sm text-white/50">
            Requêtes type « acheter [marque] réplique », Yupoo, où acheter en France.
          </p>
          <CardGrid
            items={buy.map((p) => ({
              slug: p.slug,
              title: p.h1,
              blurb: p.description,
              label: "Achat",
            }))}
          />
        </section>

        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Guides pratiques</h2>
          <p className="mt-2 text-sm text-white/50">Intentions fortes — parcours et QC.</p>
          <CardGrid
            items={howto.map((p) => ({
              slug: p.slug,
              title: p.h1,
              blurb: p.description,
              label: "Pratique",
            }))}
          />
        </section>

        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Maisons</h2>
          <CardGrid
            items={brands.map((p) => ({
              slug: p.slug,
              title: p.h1.replace(/^Guide discret\s+/i, ""),
              blurb: p.intro,
              label: "Maison",
            }))}
          />
        </section>

        <section className="mt-16">
          <h2 className="font-display text-2xl font-semibold">Modèles & niches</h2>
          <CardGrid
            items={models.map((p) => ({
              slug: p.slug,
              title: p.h1,
              blurb: p.description,
              label: "Modèle",
            }))}
          />
        </section>

        <section id="acces" className="mt-16 grid gap-8 md:grid-cols-2 md:items-start">
          <div>
            <h2 className="font-display text-2xl font-semibold">Contact direct</h2>
            <p className="mt-3 text-sm leading-relaxed text-white/60">
              Telegram pour une réponse rapide, ou formulaire. Pas de spam — uniquement l’accès
              guide et les réponses utiles.
            </p>
            <ul className="mt-6 space-y-2 text-sm text-white/55">
              <li>— Checklists QC</li>
              <li>— Parcours Yupoo / agent / WhatsApp</li>
              <li>— Tips livraison France</li>
            </ul>
          </div>
          <CaptureForm telegramUrl={TELEGRAM} source="seo:hub" />
        </section>

        <footer className="mt-20 border-t border-white/10 pt-6 text-xs text-white/35">
          LuxFind FR — entité indépendante. Contenu informatif à destination d’adultes.
        </footer>
      </main>
      <TelegramSticky telegramUrl={TELEGRAM} />
    </div>
  );
}
