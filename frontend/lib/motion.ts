// Motion tokens for framer-motion, mirroring MASTER.md and the Tailwind
// `duration-*` / `ease-assay` utilities. Seconds, because framer-motion uses seconds.
export const DURATION = { fast: 0.12, base: 0.18, slow: 0.24 } as const;

export const EASE = [0.2, 0.8, 0.2, 1] as const;

// Exits run faster than entrances so dismissals feel immediate.
export function exit(duration: number): number {
  return duration * 0.7;
}
