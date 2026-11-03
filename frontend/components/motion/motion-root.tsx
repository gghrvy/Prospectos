"use client";

import { MotionConfig } from "framer-motion";
import type { ReactNode } from "react";

import { DURATION, EASE } from "@/lib/motion";

// One place for framer-motion defaults. reducedMotion="user" drops transform
// and layout animations (keeping opacity) when the OS asks for less motion.
export function MotionRoot({ children }: { children: ReactNode }) {
  return (
    <MotionConfig reducedMotion="user" transition={{ duration: DURATION.base, ease: [...EASE] }}>
      {children}
    </MotionConfig>
  );
}
