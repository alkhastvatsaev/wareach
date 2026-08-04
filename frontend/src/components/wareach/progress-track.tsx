"use client";

import { motion, useReducedMotion } from "framer-motion";

export function ProgressTrack({
  pct,
  label,
}: {
  pct: number;
  label: string;
}) {
  const reduce = useReducedMotion();
  const width = Math.min(100, Math.max(0, pct));

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3 text-xs text-[var(--muted)]">
        <span>{label}</span>
        <span className="font-mono tabular-nums text-[var(--ink)]">{width}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--line)]">
        <motion.div
          className="h-full rounded-full bg-[var(--accent)]"
          initial={false}
          animate={{ width: `${width}%` }}
          transition={
            reduce
              ? { duration: 0 }
              : { type: "spring", stiffness: 120, damping: 22, mass: 0.8 }
          }
        />
      </div>
    </div>
  );
}
