import type { HTMLAttributes } from "react";

import { stageLabel, stageTone } from "@/lib/stages";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-tag border border-rule bg-sheet px-1.5 py-0.5 text-xs font-medium text-ink",
        className
      )}
      {...props}
    />
  );
}

function Empty() {
  return <span className="text-graphite">–</span>;
}

// Quality grades the website, not the lead: a weak site is a warning about the
// site (and usually a good opportunity), so only weak grades get color.
const QUALITY_TONE: Record<string, string> = {
  AVERAGE: "border-ochre/30 bg-ochre/[0.07] text-ochre",
  WEAK: "border-ochre/30 bg-ochre/[0.07] text-ochre",
  POOR: "border-brick/30 bg-brick/[0.07] text-brick",
  CRITICAL: "border-brick/40 bg-brick/[0.1] text-brick",
};

export function QualityBadge({ category }: { category: string | null | undefined }) {
  if (!category) return <Empty />;
  const label = category.charAt(0) + category.slice(1).toLowerCase();
  return <Badge className={QUALITY_TONE[category]}>{label}</Badge>;
}

// Every opportunity score in the app renders as this 10-tick meter: survey
// green only, so more ink always means more opportunity.
const TICK_COUNT = 10;

export function scoreWord(score: number): string {
  if (score >= 70) return "Strong";
  if (score >= 40) return "Moderate";
  return "Low";
}

export function SignalMeter({
  score,
  size = "sm",
  showWord = true,
  showNumber = true,
  revealKey,
}: {
  score: number | null | undefined;
  size?: "sm" | "lg";
  showWord?: boolean;
  showNumber?: boolean;
  // A new value refills the ticks left to right, 40ms apart. Set only after
  // a user-run audit (see ScoreGrade); never on page load.
  revealKey?: number;
}) {
  if (score === null || score === undefined) return <Empty />;
  const clamped = Math.max(0, Math.min(100, score));
  const filled = Math.round((clamped / 100) * TICK_COUNT);
  const tick = size === "lg" ? "h-3.5 w-[5px]" : "h-3 w-1";

  return (
    <span className="inline-flex items-center gap-2" aria-label={`Opportunity ${score} of 100, ${scoreWord(score).toLowerCase()}`}>
      <span className="inline-flex items-end gap-[2px]" aria-hidden="true">
        {Array.from({ length: TICK_COUNT }).map((_, i) =>
          revealKey ? (
            <span key={i} className={cn("relative overflow-hidden rounded-[1px] bg-rule", tick)}>
              {i < filled && (
                <span
                  key={revealKey}
                  className="absolute inset-0 origin-bottom animate-assay-tick bg-survey"
                  style={{ animationDelay: `${i * 40}ms` }}
                />
              )}
            </span>
          ) : (
            <span key={i} className={cn("rounded-[1px]", tick, i < filled ? "bg-survey" : "bg-rule")} />
          )
        )}
      </span>
      {showNumber && <span className="font-medium tabular-nums text-ink" aria-hidden="true">{score}</span>}
      {showWord && <span className="hidden text-xs text-graphite sm:inline" aria-hidden="true">{scoreWord(score)}</span>}
    </span>
  );
}

// Kept so existing call sites (`<OpportunityScoreBadge score={…} />`) keep working.
export const OpportunityScoreBadge = SignalMeter;

const DOT_TONE = {
  won: "bg-survey",
  closed: "bg-graphite/60",
  open: "border border-ink/60 bg-transparent",
} as const;

export function StatusBadge({ status }: { status: string | null | undefined }) {
  const tone = stageTone(status ?? null);
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap text-[13px]", tone === "closed" ? "text-graphite" : "text-ink", tone === "won" && "font-medium text-survey")}>
      <span className={cn("h-2 w-2 shrink-0 rounded-full", DOT_TONE[tone])} aria-hidden="true" />
      {stageLabel(status ?? null)}
    </span>
  );
}
