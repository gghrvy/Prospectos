"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { ArrowLeft, ChevronDown } from "lucide-react";

import { ScoreGrade, type ScoreReveal } from "@/components/lead/score-grade";
import { StageTrack } from "@/components/lead/stage-track";
import { QualityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Menu } from "@/components/ui/menu";
import { Textarea } from "@/components/ui/textarea";
import { LEAD_STATUSES, LEAD_STATUS_LABELS, type BusinessDetail, type LeadStatus } from "@/lib/types";

export function LeadHeader({
  business,
  demo,
  auditing,
  scoreReveal,
  generating,
  onGenerate,
  onAudit,
  onMove,
  onDelete,
}: {
  business: BusinessDetail;
  demo: boolean;
  auditing: boolean;
  scoreReveal: ScoreReveal | null;
  generating: boolean;
  onGenerate: () => void;
  onAudit: () => void;
  onMove: (status: LeadStatus, note: string) => Promise<boolean>;
  onDelete: () => void;
}) {
  const audit = business.latest_audit;
  const location = [business.category, [business.city, business.state].filter(Boolean).join(", ")]
    .filter(Boolean)
    .join(" in ");

  const auditLabel = auditing ? "Auditing…" : demo ? "Replay audit" : business.audits.length ? "Re-run audit" : "Run audit";

  return (
    <header className="flex flex-col gap-5">
      <Link
        href="/prospects"
        className="focus-ring -ml-1 inline-flex w-fit items-center gap-1.5 rounded-control px-1 py-0.5 text-[13px] text-graphite transition-colors duration-fast ease-assay hover:text-ink"
      >
        <ArrowLeft size={14} aria-hidden="true" />
        Leads
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-4">
        <div className="min-w-0">
          <h1 className="font-serif text-[28px] font-medium leading-[34px] tracking-[-0.01em] text-ink sm:text-[32px] sm:leading-[38px]">
            {business.name}
          </h1>
          {location && <p className="mt-1 text-sm text-graphite">{location}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={onGenerate} disabled={generating}>
            {generating ? "Writing draft…" : demo ? "View draft preview" : "Generate outreach"}
          </Button>
          <Button variant="outline" onClick={onAudit} disabled={auditing}>
            {auditLabel}
          </Button>
          {!demo && <MoveTo current={business.current_status} onMove={onMove} />}
          {!demo && (
            <Menu label="More actions" items={[{ label: "Delete lead", tone: "danger", onSelect: onDelete }]} />
          )}
        </div>
      </div>

      <Card className="grid gap-6 p-5 md:grid-cols-[auto_minmax(0,1fr)] md:items-center md:gap-10">
        <div className="flex items-end gap-6">
          <ScoreGrade score={audit?.overall_opportunity_score ?? null} label="Opportunity" reveal={scoreReveal} />
          {audit?.quality_category && (
            <div className="flex flex-col gap-1.5 pb-0.5">
              <span className="text-xs text-graphite">Website quality</span>
              <QualityBadge category={audit.quality_category} />
            </div>
          )}
        </div>
        <StageTrack status={business.current_status} />
      </Card>
    </header>
  );
}

// Picking a stage opens a small dialog for an optional note, so a status
// change is never one stray click.
function MoveTo({
  current,
  onMove,
}: {
  current: string | null;
  onMove: (status: LeadStatus, note: string) => Promise<boolean>;
}) {
  const [target, setTarget] = useState<LeadStatus | null>(null);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  // Keeps the title while the dialog animates out after target is cleared.
  const lastTarget = useRef<LeadStatus | null>(null);
  if (target) lastTarget.current = target;
  const titleTarget = target ?? lastTarget.current;

  function close() {
    setTarget(null);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!target) return;
    setSaving(true);
    const moved = await onMove(target, note.trim());
    setSaving(false);
    if (moved) close();
  }

  return (
    <>
      <Menu
        label="Move to stage"
        className="border border-rule bg-sheet text-ink"
        trigger={
          <>
            Move to
            <ChevronDown size={14} aria-hidden="true" />
          </>
        }
        items={LEAD_STATUSES.map((status) => ({
          label: LEAD_STATUS_LABELS[status],
          checked: status === current,
          disabled: status === current,
          onSelect: () => {
            // Cleared on open, not on close, so the note stays put while the dialog exits.
            setNote("");
            setTarget(status);
          },
        }))}
      />
      <Dialog open={target !== null} onClose={close} title={titleTarget ? `Move to ${LEAD_STATUS_LABELS[titleTarget]}` : ""}>
        <form onSubmit={submit} className="flex flex-col gap-4 p-4">
          <div>
            <Label htmlFor="move-note">Note (optional)</Label>
            <Textarea
              id="move-note"
              data-autofocus
              rows={3}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="What happened, e.g. replied asking for prices"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={close}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Moving…" : "Move lead"}
            </Button>
          </div>
        </form>
      </Dialog>
    </>
  );
}
