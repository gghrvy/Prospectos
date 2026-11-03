import { LEAD_STATUS_LABELS, type LeadStatus } from "@/lib/types";

// Frontend-only grouping of the 16 lead statuses into five phases, so the
// pipeline reads as a handful of columns instead of sixteen. The API still
// stores and returns the exact status; nothing here is sent back.
export type Phase = "research" | "contact" | "conversation" | "closing" | "outcome";

export const PHASES: { id: Phase; label: string; statuses: LeadStatus[] }[] = [
  { id: "research", label: "Research", statuses: ["NEW", "AUDITED", "QUALIFIED", "OUTREACH_READY"] },
  { id: "contact", label: "Contact", statuses: ["CONTACTED", "FOLLOW_UP"] },
  { id: "conversation", label: "Conversation", statuses: ["REPLIED", "INTERESTED", "CONCEPT_SENT", "DISCUSSION"] },
  { id: "closing", label: "Closing", statuses: ["DEMO_SENT", "CALL_BOOKED", "PROPOSAL"] },
  { id: "outcome", label: "Outcome", statuses: ["WON", "LOST", "NOT_INTERESTED"] },
];

// The forward sequence a lead moves through; outcomes sit outside it.
export const PROGRESS_STAGES: LeadStatus[] = PHASES.filter((phase) => phase.id !== "outcome").flatMap(
  (phase) => phase.statuses
);

// A lead with no history yet is NEW. A status this build doesn't know about
// (e.g. added server-side later) stays visible in Research rather than vanishing.
export function phaseOf(status: string | null): Phase {
  const value = status ?? "NEW";
  return PHASES.find((phase) => (phase.statuses as string[]).includes(value))?.id ?? "research";
}

export function stageIndex(status: string | null): number {
  return (PROGRESS_STAGES as string[]).indexOf(status ?? "NEW");
}

export function stageLabel(status: string | null): string {
  if (!status) return "New";
  return LEAD_STATUS_LABELS[status] ?? status.replace(/_/g, " ");
}

export type StageTone = "won" | "closed" | "open";

export function stageTone(status: string | null): StageTone {
  if (status === "WON") return "won";
  if (status === "LOST" || status === "NOT_INTERESTED") return "closed";
  return "open";
}
