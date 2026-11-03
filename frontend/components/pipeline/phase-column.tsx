"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRightLeft } from "lucide-react";

import { SignalMeter, StatusBadge } from "@/components/ui/badge";
import { Menu } from "@/components/ui/menu";
import { DURATION, EASE } from "@/lib/motion";
import { PHASES, type Phase, stageIndex } from "@/lib/stages";
import { LEAD_STATUSES, LEAD_STATUS_LABELS, type BusinessListItem, type LeadStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

// What puts a lead into each column, so an empty column still teaches the flow.
const EMPTY: Record<Phase, string> = {
  research: "Leads land here when you discover, import or add them.",
  contact: "A lead moves here once its first email is sent.",
  conversation: "Leads move here when they reply.",
  closing: "Leads move here once a demo, call or proposal is under way.",
  outcome: "Won, lost and not-interested leads end up here.",
};

const PAGE = 30;

function rank(status: string | null): number {
  return status === "WON" ? 100 : stageIndex(status);
}

export function PhaseColumn({
  phase,
  leads,
  demo,
  onMove,
}: {
  phase: Phase;
  leads: BusinessListItem[];
  demo: boolean;
  onMove: (id: string, status: LeadStatus) => Promise<void>;
}) {
  const [shown, setShown] = useState(PAGE);
  const meta = PHASES.find((p) => p.id === phase)!;
  // Furthest along first (won before lost in Outcome), then strongest opportunity.
  const sorted = [...leads].sort(
    (a, b) =>
      rank(b.current_status) - rank(a.current_status) ||
      (b.latest_opportunity_score ?? -1) - (a.latest_opportunity_score ?? -1)
  );
  const visible = sorted.slice(0, shown);
  const headingId = `${phase}-heading`;

  return (
    <section
      id={phase}
      aria-labelledby={headingId}
      className="flex min-w-0 scroll-mt-20 flex-col lg:scroll-mt-6 rounded-panel border border-rule bg-sheet xl:max-h-[calc(100dvh-180px)]"
    >
      <header className="border-b border-rule px-4 py-3">
        <div className="flex items-baseline justify-between gap-3">
          <h2 id={headingId} className="text-sm font-semibold text-ink">
            {meta.label}
          </h2>
          <span className="text-sm tabular-nums text-graphite" aria-label={`${leads.length} leads`}>
            {leads.length}
          </span>
        </div>
        <p className="mt-0.5 text-xs leading-5 text-graphite">{meta.statuses.map((s) => LEAD_STATUS_LABELS[s]).join(", ")}</p>
      </header>

      {leads.length === 0 ? (
        <p className="px-4 py-5 text-[13px] leading-5 text-graphite">{EMPTY[phase]}</p>
      ) : (
        // layoutScroll: rows measured inside this scroller stay correct when it is scrolled.
        <motion.div layoutScroll className="min-h-0 flex-1 xl:overflow-y-auto">
          <ul className="divide-y divide-rule/70">
            {visible.map((lead) => (
              <LeadRow key={lead.id} lead={lead} demo={demo} onMove={onMove} />
            ))}
          </ul>
          {sorted.length > shown && (
            <button
              type="button"
              onClick={() => setShown((n) => n + PAGE)}
              className="focus-ring w-full border-t border-rule/70 px-4 py-2.5 text-left text-[13px] text-survey transition-colors duration-fast ease-assay hover:bg-survey/[0.04]"
            >
              Show {Math.min(PAGE, sorted.length - shown)} more of {sorted.length - shown}
            </button>
          )}
        </motion.div>
      )}
    </section>
  );
}

function LeadRow({
  lead,
  demo,
  onMove,
}: {
  lead: BusinessListItem;
  demo: boolean;
  onMove: (id: string, status: LeadStatus) => Promise<void>;
}) {
  const [moving, setMoving] = useState(false);

  async function move(status: LeadStatus) {
    setMoving(true);
    try {
      await onMove(lead.id, status);
    } finally {
      setMoving(false);
    }
  }

  // One layoutId per lead across all columns: a moved lead slides from its
  // old column to its new one. "position" so the text never scales mid-move.
  return (
    <motion.li
      layoutId={`pipeline-${lead.id}`}
      layout="position"
      transition={{ duration: DURATION.slow, ease: [...EASE] }}
      className={cn("group relative flex items-start gap-2 px-4 py-3 transition-colors duration-fast ease-assay hover:bg-survey/[0.04]", moving && "opacity-60")}>
      <div className="min-w-0 flex-1">
        {/* The name link covers the row; the menu sits above it. */}
        <Link
          href={`/prospects/${lead.id}`}
          className="focus-ring line-clamp-2 rounded-[2px] font-serif text-[15px] font-medium leading-6 text-ink after:absolute after:inset-0 after:content-['']"
        >
          {lead.name}
        </Link>
        <div className="mt-1 flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
          <StatusBadge status={lead.current_status} />
          {lead.latest_opportunity_score !== null && lead.latest_opportunity_score !== undefined && (
            <SignalMeter score={lead.latest_opportunity_score} showWord={false} />
          )}
        </div>
      </div>
      {!demo && (
        <div className="relative z-[1] -mr-2 -mt-1">
          <Menu
            label={`Move ${lead.name}`}
            icon={<ArrowRightLeft size={14} aria-hidden="true" />}
            className="text-graphite opacity-60 group-hover:opacity-100 focus-visible:opacity-100 aria-expanded:opacity-100"
            items={LEAD_STATUSES.map((status) => ({
              label: LEAD_STATUS_LABELS[status],
              checked: status === (lead.current_status ?? "NEW"),
              disabled: moving || status === (lead.current_status ?? "NEW"),
              onSelect: () => void move(status),
            }))}
          />
        </div>
      )}
    </motion.li>
  );
}
