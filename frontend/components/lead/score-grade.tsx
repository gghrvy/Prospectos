"use client";

import { useLayoutEffect, useRef } from "react";
import { animate, useReducedMotion } from "framer-motion";

import { scoreWord, SignalMeter } from "@/components/ui/badge";
import { EASE } from "@/lib/motion";

export interface ScoreReveal {
  // The score shown before the audit ran; null when it's the first audit.
  from: number | null;
  // Bumped once per finished audit so a re-run with the same score still plays.
  key: number;
}

const COUNT_SECONDS = 0.6;

// The lead's grade as an assay stamp: a serif numeral, the tick meter, a word.
// After a user-run audit the numeral counts from the old score to the new one
// while the ticks refill; on page load it simply shows the score.
export function ScoreGrade({ score, label, reveal }: { score: number | null; label: string; reveal?: ScoreReveal | null }) {
  const numeral = useRef<HTMLSpanElement>(null);
  const reduceMotion = useReducedMotion();
  const revealKey = reveal?.key;
  // A first audit, or a re-run that lands on the same score (always the case
  // for the demo replay), re-stamps the grade from zero so the count still reads.
  const revealFrom = reveal?.from === null || reveal?.from === undefined || reveal.from === score ? 0 : reveal.from;

  // Layout effect: the starting number is in place before the first frame is
  // painted, so the final score never flashes first. The count writes straight
  // to the DOM (no React state per frame).
  useLayoutEffect(() => {
    const el = numeral.current;
    if (!revealKey || score === null || !el || reduceMotion) return;
    el.textContent = String(revealFrom);
    const controls = animate(revealFrom, score, {
      duration: COUNT_SECONDS,
      ease: [...EASE],
      onUpdate: (value) => {
        el.textContent = String(Math.round(value));
      },
    });
    return () => {
      controls.stop();
      el.textContent = String(score);
    };
  }, [revealKey, revealFrom, score, reduceMotion]);

  return (
    <div className="flex items-end gap-4">
      <span ref={numeral} className="font-serif text-[40px] font-medium leading-none tabular-nums text-ink">
        {score ?? "–"}
      </span>
      <div className="flex flex-col gap-1.5 pb-0.5">
        <span className="text-xs text-graphite">{label}</span>
        {score === null ? (
          <span className="text-[13px] text-graphite">Not audited yet</span>
        ) : (
          <span className="flex items-center gap-2">
            <SignalMeter
              score={score}
              size="lg"
              showWord={false}
              showNumber={false}
              revealKey={reduceMotion ? undefined : revealKey}
            />
            <span className="text-[13px] font-medium text-ink">{scoreWord(score)}</span>
          </span>
        )}
      </div>
    </div>
  );
}
