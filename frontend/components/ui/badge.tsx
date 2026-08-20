import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wider",
        className
      )}
      {...props}
    />
  );
}

// Score/category color coding used across the dashboard, prospects table,
// and prospect detail page — one stoplight scale, defined once, so a color
// always means the same real thing everywhere it appears.
const QUALITY_COLORS: Record<string, string> = {
  EXCELLENT: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  GOOD: "bg-emerald-500/10 text-emerald-400/90 border-emerald-500/20",
  AVERAGE: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  WEAK: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  POOR: "bg-red-500/15 text-red-400 border-red-500/30",
  CRITICAL: "bg-red-600/20 text-red-400 border-red-600/40",
};

export function QualityBadge({ category }: { category: string | null | undefined }) {
  if (!category) return <span className="font-mono text-xs text-muted-foreground">—</span>;
  return <Badge className={QUALITY_COLORS[category] ?? ""}>{category}</Badge>;
}

// The signature element: a 10-tick signal meter standing in for every
// numeric score in the app (opportunity scores, quality score, sub-scores).
// ProspectOS's whole job is turning a crawl into a legible signal — a bare
// number or a colored pill says less at a glance than a filled meter does,
// and it reads consistently whether it's 4px tall in a table cell or large
// on the detail page.
const TICK_COUNT = 10;

function meterColor(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
}

export function SignalMeter({
  score,
  size = "sm",
}: {
  score: number | null | undefined;
  size?: "sm" | "lg";
}) {
  if (score === null || score === undefined) {
    return <span className="font-mono text-xs text-muted-foreground">—</span>;
  }
  const filled = Math.round((Math.max(0, Math.min(100, score)) / 100) * TICK_COUNT);
  const color = meterColor(score);
  const tickClass = size === "lg" ? "h-3 w-1.5" : "h-2.5 w-1";

  return (
    <span className="inline-flex items-center gap-2 font-mono">
      <span className="inline-flex items-end gap-[2px]" aria-hidden="true">
        {Array.from({ length: TICK_COUNT }).map((_, i) => (
          <span
            key={i}
            className={cn(
              "rounded-[1px] transition-colors",
              tickClass,
              i < filled ? color.replace("text-", "bg-") : "bg-border"
            )}
          />
        ))}
      </span>
      <span className={cn("tabular-nums", color, size === "lg" ? "text-lg font-semibold" : "text-sm font-medium")}>
        {score}
      </span>
    </span>
  );
}

// Kept as an alias so existing call sites (`<OpportunityScoreBadge score={…} />`)
// don't need touching one-by-one — same component, meter-based rendering.
export const OpportunityScoreBadge = SignalMeter;

const STATUS_COLORS: Record<string, string> = {
  NEW: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  AUDITED: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  QUALIFIED: "bg-emerald-500/10 text-emerald-400/90 border-emerald-500/20",
  CONTACTED: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
  FOLLOW_UP: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
  REPLIED: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  DEMO_SENT: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  CALL_BOOKED: "bg-fuchsia-500/15 text-fuchsia-400 border-fuchsia-500/30",
  PROPOSAL: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  WON: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  LOST: "bg-red-500/15 text-red-400 border-red-500/30",
  NOT_INTERESTED: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <Badge className="bg-slate-500/15 text-slate-300 border-slate-500/30">NEW</Badge>;
  return <Badge className={STATUS_COLORS[status] ?? ""}>{status.replace(/_/g, " ")}</Badge>;
}
