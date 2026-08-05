import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CaptureForm } from "@/components/luxfind/capture-form";
import { BRAND_GUIDES, getBrand } from "@/lib/luxfind-brands";

type Props = { params: Promise<{ brand: string }> };

export async function generateStaticParams() {
  return BRAND_GUIDES.map((b) => ({ brand: b.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { brand } = await params;
  const g = getBrand(brand);
  if (!g) return { title: "LuxFind FR" };
  return {
    title: `${g.headline} — LuxFind FR`,
    description: g.intro,
  };
}

const TELEGRAM = process.env.NEXT_PUBLIC_FACADE_TELEGRAM_URL || "https://t.me/luxfindfr";

export default async function BrandGuidePage({ params }: Props) {
  const { brand } = await params;
  const g = getBrand(brand);
  if (!g) notFound();

  return (
    <div className="min-h-screen bg-[#060b10] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(13,115,119,0.14),_transparent_55%)]" />
      <main className="relative mx-auto max-w-3xl px-5 py-14 md:px-8 md:py-20">
        <Link href="/guide" className="text-[11px] uppercase tracking-[0.2em] text-teal-300/80">
          ← LuxFind FR
        </Link>
        <h1 className="font-display mt-4 text-4xl font-bold tracking-tight md:text-5xl">{g.headline}</h1>
        <p className="mt-4 text-base leading-relaxed text-white/65">{g.intro}</p>

        <section className="mt-10 space-y-4">
          <h2 className="font-display text-xl font-semibold">Repères</h2>
          <ul className="space-y-3">
            {g.tips.map((t) => (
              <li
                key={t}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white/70"
              >
                {t}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-12">
          <h2 className="font-display mb-4 text-xl font-semibold">Accès guide {g.name}</h2>
          <CaptureForm brandInterest={g.slug.replace(/-/g, "_")} telegramUrl={TELEGRAM} />
        </section>

        <div className="mt-10 flex flex-wrap gap-2">
          {BRAND_GUIDES.filter((b) => b.slug !== g.slug)
            .slice(0, 4)
            .map((b) => (
              <Link
                key={b.slug}
                href={`/guide/${b.slug}`}
                className="rounded-full border border-white/15 px-3 py-1.5 text-xs text-white/50 hover:text-white/80"
              >
                {b.name}
              </Link>
            ))}
        </div>
      </main>
    </div>
  );
}
