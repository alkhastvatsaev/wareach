"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function LiveDot({
  ok,
  label,
}: {
  ok: boolean | null;
  label: string;
}) {
  const tone =
    ok === null ? "bg-[var(--muted)]" : ok ? "bg-emerald-500" : "bg-rose-500";

  return (
    <span className="inline-flex items-center gap-2 text-xs text-[var(--muted)]">
      <span className="relative flex h-2 w-2">
        {ok && (
          <motion.span
            className={cn("absolute inline-flex h-full w-full rounded-full opacity-60", tone)}
            animate={{ scale: [1, 2.2], opacity: [0.55, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
          />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", tone)} />
      </span>
      {label}
    </span>
  );
}
