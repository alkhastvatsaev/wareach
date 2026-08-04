"use client";

import { animate, motion, useMotionValue, useReducedMotion, useTransform } from "framer-motion";
import { useEffect } from "react";

export function AnimatedNumber({
  value,
  className,
}: {
  value: number | null;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const mv = useMotionValue(0);
  const display = useTransform(mv, (v) =>
    value == null ? "—" : Math.round(v).toLocaleString("fr-FR")
  );

  useEffect(() => {
    if (value == null) {
      mv.set(0);
      return;
    }
    if (reduce) {
      mv.set(value);
      return;
    }
    const controls = animate(mv, value, {
      duration: 0.9,
      ease: [0.16, 1, 0.3, 1],
    });
    return controls.stop;
  }, [value, mv, reduce]);

  if (value == null) {
    return <span className={className}>—</span>;
  }

  return <motion.span className={className}>{display}</motion.span>;
}
