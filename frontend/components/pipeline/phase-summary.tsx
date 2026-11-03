import Link from "next/link";

import { PHASES, phaseOf, type Phase } from "@/lib/stages";
import type { BusinessListItem } from "@/lib/types";

export function countByPhase(businesses: BusinessListItem[]): Record<Phase, number> {
  const counts = Object.fromEntries(PHASES.map((phase) => [phase.id, 0])) as Record<Phase, number>;
  for (const business of businesses) counts[phaseOf(business.current_status)] += 1;
  return counts;
}

// Five phase totals across every lead, each a way into that Pipeline column.
// The bar underneath is the same split drawn to scale, darker as leads move on.
// It stays ink: the outcome phase holds lost leads too, so it can't be green.
export function PhaseSummary({ businesses }: { businesses: BusinessListItem[] }) {
  const counts = countByPhase(businesses);
  const total = businesses.length;

  return (
    <div>
      <ol className="grid grid-cols-2 gap-px overflow-hidden rounded-panel border border-rule bg-rule sm:grid-cols-5">
        {PHASES.map((phase) => (
          <li key={phase.id} className="bg-sheet last:col-span-2 sm:last:col-span-1">
            <Link
              href={`/pipeline#${phase.id}`}
              className="focus-ring group flex h-full flex-col gap-1 px-4 py-3 transition-colors duration-fast ease-assay hover:bg-survey/[0.04]"
            >
              <span className="text-[13px] text-graphite group-hover:text-ink">{phase.label}</span>
              <span className="text-2xl font-medium tabular-nums text-ink">{counts[phase.id]}</span>
            </Link>
          </li>
        ))}
      </ol>
      {total > 0 && (
        <div className="mt-3 flex h-1.5 gap-0.5 overflow-hidden rounded-full" aria-hidden="true">
          {PHASES.map((phase, i) =>
            counts[phase.id] === 0 ? null : (
              <span
                key={phase.id}
                className="bg-ink"
                style={{ flexGrow: counts[phase.id], opacity: 0.16 + i * 0.16 }}
              />
            )
          )}
        </div>
      )}
    </div>
  );
}
