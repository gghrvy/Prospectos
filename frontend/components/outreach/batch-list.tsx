"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Menu, type MenuItem } from "@/components/ui/menu";
import { useToast } from "@/components/ui/toast";
import { activityTime } from "@/lib/activity";
import { ApiError, type api } from "@/lib/api";
import { cn } from "@/lib/utils";

export type Batch = Awaited<ReturnType<typeof api.listOutreachBatches>>[number];
export type BatchAction = "pause" | "resume" | "cancel";

const STATUS: Record<string, { label: string; className: string }> = {
  ACTIVE: { label: "Ready to send", className: "font-medium text-ink" },
  PAUSED: { label: "Paused", className: "text-ochre" },
  COMPLETE: { label: "Finished", className: "text-graphite" },
  CANCELLED: { label: "Cancelled", className: "text-graphite" },
};

function statusOf(status: string) {
  return STATUS[status] ?? { label: status.charAt(0) + status.slice(1).toLowerCase(), className: "text-graphite" };
}

// Batches send only when someone presses Send. The backend enforces the send
// window and the daily and hourly limits; this list just reports what it said.
export function BatchList({
  batches,
  remainingToday,
  onDispatch,
  onControl,
}: {
  batches: Batch[];
  remainingToday: number | null;
  onDispatch: (batch: Batch) => Promise<string>;
  onControl: (batch: Batch, action: BatchAction) => Promise<void>;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule px-4 py-3">
        <h2 className="text-base font-semibold text-ink">Batches</h2>
        {remainingToday !== null && (
          <p className="text-[13px] text-graphite">
            <span className="tabular-nums text-ink">{remainingToday}</span> more can go out today
          </p>
        )}
      </div>
      {batches.length === 0 ? (
        <EmptyState bare title="No batches yet" body="Select drafts that are ready to send in the approval queue, then name the batch." />
      ) : (
        <ul>
          {batches.map((batch) => (
            <BatchRow key={batch.id} batch={batch} onDispatch={onDispatch} onControl={onControl} />
          ))}
        </ul>
      )}
    </Card>
  );
}

function BatchRow({
  batch,
  onDispatch,
  onControl,
}: {
  batch: Batch;
  onDispatch: (batch: Batch) => Promise<string>;
  onControl: (batch: Batch, action: BatchAction) => Promise<void>;
}) {
  const confirm = useConfirm();
  const rowRef = useRef<HTMLLIElement>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const status = statusOf(batch.status);
  const drafts = `${batch.count} ${batch.count === 1 ? "draft" : "drafts"}`;

  async function run(work: () => Promise<string | void>) {
    setBusy(true);
    try {
      const text = await work();
      if (text) toast(text);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "The batch couldn't be updated. Try again.", "error");
    } finally {
      setBusy(false);
      // Pause, resume and cancel remove the control that had focus; keep the
      // keyboard in this row instead of dropping it to the page.
      requestAnimationFrame(() => {
        if (!rowRef.current?.contains(document.activeElement)) rowRef.current?.focus();
      });
    }
  }

  async function send() {
    const ok = await confirm({
      title: `Send ${batch.name} now?`,
      body: "Approved drafts in this batch go out through Gmail now, up to today's remaining limit. Anything over the limit waits for the next send. Sent emails can't be unsent.",
      confirmLabel: "Send batch",
    });
    if (ok) await run(() => onDispatch(batch).then((text) => `${batch.name}: ${text}`));
  }

  async function cancel() {
    const ok = await confirm({
      title: `Cancel ${batch.name}?`,
      body: "Drafts that haven't been sent go back to the approval queue. Emails already sent stay sent.",
      confirmLabel: "Cancel batch",
      tone: "danger",
    });
    if (ok) await run(() => onControl(batch, "cancel").then(() => `${batch.name} cancelled. Unsent drafts are back in the approval queue.`));
  }

  const menu: MenuItem[] = [];
  if (batch.status === "ACTIVE") menu.push({ label: "Pause", onSelect: () => void run(() => onControl(batch, "pause").then(() => `${batch.name} paused.`)) });
  if (batch.status === "ACTIVE" || batch.status === "PAUSED") {
    menu.push({ label: "Cancel batch", tone: "danger", onSelect: () => void cancel() });
  }

  return (
    <li ref={rowRef} tabIndex={-1} aria-label={batch.name} className={cn("border-t border-rule/70 px-4 py-3 outline-none first:border-t-0 focus-visible:bg-ink/[0.03]", busy && "opacity-60")}>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink">{batch.name}</p>
          <p className="text-xs text-graphite">
            {drafts}, created {activityTime(batch.created_at)}, sends on {batch.timezone} time
          </p>
        </div>
        <span className={cn("text-[13px]", status.className)}>{status.label}</span>
        {(batch.status === "ACTIVE" || batch.status === "PAUSED") && (
          <div className="flex items-center gap-1">
            {batch.status === "ACTIVE" ? (
              <Button size="sm" variant="outline" disabled={busy} onClick={() => void send()}>
                {busy ? "Working…" : "Send"}
              </Button>
            ) : (
              <Button size="sm" variant="outline" disabled={busy} onClick={() => void run(() => onControl(batch, "resume").then(() => `${batch.name} resumed.`))}>
                Resume
              </Button>
            )}
            <Menu label={`More actions for ${batch.name}`} items={menu} />
          </div>
        )}
      </div>
    </li>
  );
}
