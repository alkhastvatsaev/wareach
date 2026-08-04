"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export function BentoGrid({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={cn(
        "grid w-full grid-cols-1 gap-3 md:grid-cols-6 md:auto-rows-[minmax(7.5rem,auto)] md:gap-4",
        className
      )}
      initial={reduce ? false : "hidden"}
      animate="show"
      variants={{
        hidden: {},
        show: {
          transition: { staggerChildren: reduce ? 0 : 0.07 },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

export function BentoCell({
  children,
  className,
  span = "md:col-span-2",
}: {
  children: React.ReactNode;
  className?: string;
  span?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: reduce ? 0 : 18, scale: reduce ? 1 : 0.98 },
        show: {
          opacity: 1,
          y: 0,
          scale: 1,
          transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] },
        },
      }}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/12 bg-black/35 backdrop-blur-md",
        "shadow-[0_12px_40px_-20px_rgba(0,0,0,0.55)]",
        span,
        className
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(420px_180px_at_100%_0%,var(--glow),transparent_60%)]" />
      <div className="relative z-10 h-full p-5 md:p-6">{children}</div>
    </motion.div>
  );
}
