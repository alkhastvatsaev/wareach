import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CaptureForm } from "@/components/luxfind/capture-form";
import { TelegramSticky } from "@/components/luxfind/telegram-sticky";
import { LUXFIND_PAGES, getPage, relatedPages } from "@/lib/luxfind-pages";

type Props = { params: Promise<{ slug: string }> };

const TELEGRAM = process.env.NEXT_PUBLIC_FACADE_TELEGRAM_URL || "https://t.me/luxfindfr";
const SITE = process.env.NEXT_PUBLIC_SITE_URL || "https://wareach.vercel.app";

export async function generateStaticParams() {
  return LUXFIND_PAGES.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const g = getPage(slug);
  if (!g) return { title: "LuxFind FR" };
  const url = `${SITE}/guide/${g.slug}`;
  return {
    title: `${g.title} | LuxFind FR`,
    description: g.description,
    alternates: { canonical: url },
    openGraph: {
      title: g.h1,
      description: g.description,
      url,
      locale: "fr_FR",
      type: "article",
    },
  };
}

export default async function GuideSlugPage({ params }: Props) {
  const { slug } = await params;
  const g = getPage(slug);
  if (!g) notFound();

  const related = relatedPages(g);
  const brandInterest = g.brands?.[0] || (g.intent === "brand" ? g.slug.replace(/-/g, "_") : undefined);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: g.h1,
    description: g.description,
    inLanguage: "fr-FR",
    author: { "@type": "Organization", name: "LuxFind FR" },
    mainEntityOfPage: `${SITE}/guide/${g.slug}`,
  };

  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: g.sections.map((s) => ({
      "@type": "Question",
      name: s.h2,
      acceptedAnswer: { "@type": "Answer", text: s.body },
    })),
  };

  return (
    <div className="min-h-screen bg-[#060b10] pb-24 text-white md:pb-0">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(13,115,119,0.14),_transparent_55%)]" />
      <main className="relative mx-auto max-w-3xl px-5 py-14 md:px-8 md:py-20">
        <Link href="/guide" className="text-[11px] uppercase tracking-[0.2em] text-teal-300/80">
          ← LuxFind FR
        </Link>
        <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/40">
          {g.intent === "howto"
            ? "Guide pratique"
            : g.intent === "brand"
              ? "Maison"
              : g.intent === "buy"
                ? "Achat"
                : "Modèle"}
        </p>
        <h1 className="font-display mt-2 text-4xl font-bold tracking-tight md:text-5xl">{g.h1}</h1>
        <p className="mt-4 text-base leading-relaxed text-white/65">{g.intro}</p>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={TELEGRAM}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-full bg-[var(--accent)] px-5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            Contacter sur Telegram
          </a>
          <a
            href="#contact"
            className="inline-flex min-h-11 items-center rounded-full border border-white/20 px-5 text-sm font-medium text-white/80"
          >
            Laisser un contact
          </a>
        </div>

        <div className="mt-12 space-y-8">
          {g.sections.map((s) => (
            <section key={s.h2}>
              <h2 className="font-display text-xl font-semibold">{s.h2}</h2>
              <p className="mt-3 text-sm leading-relaxed text-white/70 md:text-base">{s.body}</p>
            </section>
          ))}
        </div>

        <section id="contact" className="mt-14">
          <h2 className="font-display mb-4 text-xl font-semibold">Accès guide — contact direct</h2>
          <p className="mb-4 text-sm text-white/55">
            Telegram pour une réponse rapide, ou formulaire email. On vous recontacte discrètement.
          </p>
          <CaptureForm
            brandInterest={brandInterest}
            telegramUrl={TELEGRAM}
            source={`seo:${g.slug}`}
          />
        </section>

        {related.length > 0 && (
          <section className="mt-12">
            <h2 className="font-display text-lg font-semibold">Continuer</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {related.map((r) => (
                <Link
                  key={r.slug}
                  href={`/guide/${r.slug}`}
                  className="rounded-full border border-white/15 px-3 py-1.5 text-xs text-white/55 transition hover:border-teal-400/40 hover:text-white/85"
                >
                  {r.h1.length > 42 ? `${r.h1.slice(0, 40)}…` : r.h1}
                </Link>
              ))}
              <Link
                href="/guide"
                className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-white/35 hover:text-white/60"
              >
                Tous les guides
              </Link>
            </div>
          </section>
        )}

        <footer className="mt-16 border-t border-white/10 pt-6 text-xs text-white/35">
          LuxFind FR — contenu informatif. Entité indépendante.
        </footer>
      </main>
      <TelegramSticky telegramUrl={TELEGRAM} />
    </div>
  );
}
