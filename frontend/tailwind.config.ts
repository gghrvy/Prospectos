import type { Config } from "tailwindcss";

// Tokens mirror frontend/MASTER.md. Components use these names only.
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: token("paper"),
        sheet: token("sheet"),
        ink: token("ink"),
        graphite: token("graphite"),
        rule: token("rule"),
        survey: token("survey"),
        ochre: token("ochre"),
        brick: token("brick"),
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "ui-serif", "Georgia", "serif"],
      },
      borderRadius: {
        tag: "4px",
        control: "6px",
        panel: "10px",
      },
      boxShadow: {
        float: "0 1px 2px rgb(28 31 29 / 0.06), 0 8px 24px rgb(28 31 29 / 0.10)",
      },
      transitionDuration: {
        fast: "120ms",
        base: "180ms",
        slow: "240ms",
      },
      transitionTimingFunction: {
        assay: "cubic-bezier(0.2, 0.8, 0.2, 1)",
      },
      // Skeleton pulse. Frozen by the reduced-motion rule in globals.css.
      keyframes: {
        "assay-pulse": { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0.45" } },
        "assay-enter": { from: { opacity: "0", transform: "translateY(4px)" }, to: { opacity: "1", transform: "none" } },
        "assay-tick": { from: { opacity: "0", transform: "scaleY(0.4)" }, to: { opacity: "1", transform: "none" } },
      },
      animation: {
        "assay-pulse": "assay-pulse 1.2s ease-in-out infinite",
        // No fill-mode "forwards": a leftover transform would become the
        // containing block for position:fixed children (selection bars).
        "assay-enter": "assay-enter 180ms cubic-bezier(0.2, 0.8, 0.2, 1)",
        "assay-tick": "assay-tick 180ms cubic-bezier(0.2, 0.8, 0.2, 1) backwards",
      },
    },
  },
  plugins: [],
};

export default config;
