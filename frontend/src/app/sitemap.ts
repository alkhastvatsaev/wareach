import type { MetadataRoute } from "next";
import { LUXFIND_PAGES } from "@/lib/luxfind-pages";

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "https://wareach.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    {
      url: `${SITE}/guide`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
    },
    ...LUXFIND_PAGES.map((p) => ({
      url: `${SITE}/guide/${p.slug}`,
      lastModified: now,
      changeFrequency: "weekly" as const,
      priority: p.intent === "howto" ? 0.9 : 0.7,
    })),
  ];
}
