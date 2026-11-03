"use client";

import { motion } from "framer-motion";

import { DURATION, EASE } from "@/lib/motion";
import { PHASES, phaseOf, PROGRESS_STAGES, stageIndex, stageLabel } from "@/lib/stages";
import { cn } from "@/lib/utils";

const STEPS = PROGRESS_STAGES.length;
const FORWARD_PHASES = PHASES.filter((phase) => phase.id !== "outcome");

// The 13 forward stages as a survey line of stations, grouped by phase, with
// the outcome as an end cap. Reached stations are ink, the current one survey.
// The current-station marker is one shared layout element, so a stage change
// slides it along the line instead of swapping dots.
export function StageTrack({ status, className }: { status: string | null; className?: string }) {
  const index = stageIndex(status);
  const phase = phaseOf(status);
  const isOutcome = phase === "outcome";
  const won = status === "WON";
  // An unknown status still sits in Research (see phaseOf); draw it at the start.
  const position = isOutcome ? (won ? STEPS : -1) : Math.max(index, 0);
  const label = stageLabel(status);
  const step = isOutcome ? "Final outcome" : `Step ${position + 1} of ${STEPS}`;
  const phaseLabel = PHASES.find((p) => p.id === phase)?.label ?? "";

  let cursor = 0;
  return (
    <div className={cn("w-full", className)} role="img" aria-label={`Stage: ${label}, ${step.toLowerCase()}`}>
      <div className="flex items-baseline justify-between gap-3 text-[13px]" aria-hidden="true">
        <span className={cn("font-medium", isOutcome && !won ? "text-graphite" : won ? "text-survey" : "text-ink")}>{label}</span>
        <span className="text-xs tabular-nums text-graphite">
          {isOutcome ? step : `${phaseLabel}, ${step.toLowerCase()}`}
        </span>
      </div>
      <div
        className="mt-2.5 grid items-start gap-0"
        style={{ gridTemplateColumns: `${FORWARD_PHASES.map((p) => `${p.statuses.length}fr`).join(" ")} auto` }}
        aria-hidden="true"
      >
        {FORWARD_PHASES.map((group) => (
          <div key={group.id} className="min-w-0">
            <div className="flex items-center">
              {group.statuses.map((stage) => {
                const i = cursor++;
                const reached = i < position;
                const current = i === position;
                return (
                  <span key={stage} className="flex flex-1 items-center">
                    <span
                      className={cn(
                        "relative h-2.5 w-2.5 shrink-0 rounded-full border transition-colors duration-slow ease-assay",
                        reached ? "border-ink bg-ink" : "border-rule bg-sheet"
                      )}
                    >
                      {current && (
                        <motion.span
                          layoutId="stage-marker"
                          transition={{ duration: DURATION.slow, ease: [...EASE] }}
                          className="absolute -inset-px rounded-full border border-survey bg-sheet"
                        >
                          <span className="absolute inset-[2px] rounded-full bg-survey" />
                        </motion.span>
                      )}
                    </span>
                    <span className={cn("h-px flex-1 transition-colors duration-slow ease-assay", reached ? "bg-ink" : "bg-rule")} />
                  </span>
                );
              })}
            </div>
          </div>
        ))}
        <div>
          <span
            className={cn(
              "block h-2.5 w-2.5 rounded-[2px] border",
              won ? "border-survey bg-survey" : isOutcome ? "border-graphite bg-graphite/60" : "border-rule bg-sheet"
            )}
          />
        </div>
      </div>
    </div>
  );
}
