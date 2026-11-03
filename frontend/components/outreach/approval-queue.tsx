"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { activityTime } from "@/lib/activity";
import { ApiError, type api } from "@/lib/api";
import { cn } from "@/lib/utils";

export type ApprovalItem = Awaited<ReturnType<typeof api.outreachApprovalQueue>>["items"][number];

// The newest unsent draft per lead. Only drafts someone approved can be put
// in a batch; the rest link back to the lead to be reviewed there.
export function ApprovalQueue({
  items,
  demo = false,
  onCreateBatch,
}: {
  items: ApprovalItem[];
  demo?: boolean;
  onCreateBatch?: (name: string, ids: string[]) => Promise<void>;
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ready = items.filter((item) => item.approval_status === "APPROVED");
  // Drop ids that left the queue (sent, batched elsewhere) since the last load.
  const chosen = ready.filter((item) => selected.has(item.outreach_id)).map((item) => item.outreach_id);
  const allChosen = ready.length > 0 && chosen.length === ready.length;

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function create(event: React.FormEvent) {
    event.preventDefault();
    if (!onCreateBatch) return;
    if (!name.trim()) {
      setError("Name the batch so you can find it in the list below.");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      await onCreateBatch(name.trim(), chosen);
      setName("");
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The batch couldn't be created. Try again.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule px-4 py-3">
        <div className="flex items-center gap-3">
          {!demo && (
            <Checkbox
              aria-label="Select every draft that's ready to send"
              checked={allChosen}
              disabled={ready.length === 0}
              ref={(el) => {
                if (el) el.indeterminate = chosen.length > 0 && !allChosen;
              }}
              onChange={() => setSelected(allChosen ? new Set() : new Set(ready.map((item) => item.outreach_id)))}
            />
          )}
          <h2 className="text-base font-semibold text-ink">Approval queue</h2>
        </div>
        <p className="text-[13px] text-graphite">
          {items.length === 0
            ? "Nothing waiting"
            : `${ready.length} ready to send, ${items.length - ready.length} to review`}
        </p>
      </div>

      {items.length === 0 ? (
        <EmptyState
          bare
          title="No drafts waiting"
          body="Write a draft from a lead's Outreach tab. It waits here until someone approves it."
          action={
            <Link href="/prospects" className="focus-ring rounded-[2px] text-sm text-survey underline-offset-2 hover:underline">
              Open Leads
            </Link>
          }
        />
      ) : (
        <ul>
          {items.map((item) => {
            const approved = item.approval_status === "APPROVED";
            const checkboxId = `queue-${item.outreach_id}`;
            return (
              <li
                key={item.outreach_id}
                className={cn(
                  "flex items-start gap-3 border-t border-rule/70 px-4 py-3 first:border-t-0",
                  selected.has(item.outreach_id) && approved && "bg-survey/[0.04]"
                )}
              >
                {!demo && (
                  <Checkbox
                    id={checkboxId}
                    className="mt-1"
                    aria-label={approved ? `Select ${item.business_name}` : `${item.business_name} needs review before it can be batched`}
                    disabled={!approved}
                    checked={approved && selected.has(item.outreach_id)}
                    onChange={() => toggle(item.outreach_id)}
                  />
                )}
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/prospects/${item.business_id}?tab=outreach`}
                    className="focus-ring rounded-[2px] font-serif text-[15px] font-medium leading-6 text-ink hover:underline"
                  >
                    {item.business_name}
                  </Link>
                  <p className="truncate text-[13px] text-ink">{item.subject ?? "No subject"}</p>
                  <p className="truncate text-xs text-graphite">
                    To {item.email}, written {activityTime(item.created_at)}
                  </p>
                </div>
                <span className={cn("shrink-0 pt-0.5 text-[13px]", approved ? "font-medium text-ink" : "text-ochre")}>
                  {approved ? "Ready to send" : "Needs review"}
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {!demo && chosen.length > 0 && (
        <form onSubmit={create} className="flex flex-col gap-2 border-t border-rule bg-paper/60 px-4 py-3">
          <Label htmlFor="batch-name">Batch name</Label>
          <div className="flex flex-wrap gap-2">
            <Input
              id="batch-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Dentists, first week"
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "batch-error" : undefined}
              className="min-w-0 flex-1 sm:max-w-xs"
            />
            <Button type="submit" disabled={creating}>
              {creating ? "Creating batch…" : `Create batch of ${chosen.length}`}
            </Button>
          </div>
          {error && (
            <p id="batch-error" role="alert" className="text-[13px] text-brick">
              {error}
            </p>
          )}
          <p className="text-xs leading-5 text-graphite">
            Nothing sends yet. A batch sends only when you press Send, inside its hours and your daily and hourly limits.
          </p>
        </form>
      )}
    </Card>
  );
}
