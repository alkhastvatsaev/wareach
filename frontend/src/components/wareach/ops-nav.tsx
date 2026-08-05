"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "Supply" },
  { href: "/demand", label: "Demand" },
];

export function OpsNav() {
  const pathname = usePathname();
  return (
    <nav className="mb-6 flex flex-wrap items-center gap-2">
      {LINKS.map((l) => {
        const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            className={cn(
              "rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] transition",
              active
                ? "border-teal-400/50 bg-teal-400/15 text-teal-200"
                : "border-white/15 bg-white/5 text-white/55 hover:border-white/30 hover:text-white/85"
            )}
          >
            {l.label}
          </Link>
        );
      })}
      <Link
        href="/guide"
        className="ml-auto rounded-full border border-white/10 px-3 py-1.5 text-[11px] font-medium tracking-wide text-white/40 transition hover:text-white/70"
      >
        LuxFind FR →
      </Link>
    </nav>
  );
}
