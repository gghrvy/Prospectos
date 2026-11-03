"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ActivityFeed, type GmailActivity } from "@/components/outreach/activity-feed";
import { ApprovalQueue, type ApprovalItem } from "@/components/outreach/approval-queue";
import { BatchList, type Batch, type BatchAction } from "@/components/outreach/batch-list";
import { DemoNotice, PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingRegion, Skeleton, SkeletonRows } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";
import { fetchAllBusinesses } from "@/lib/fetch-all";
import { isDemoMode } from "@/lib/runtime";

type GmailReport = Awaited<ReturnType<typeof api.gmailReport>>;

export default function OutreachPage() {
  return isDemoMode ? <DemoOutreach /> : <LiveOutreach />;
}

function LiveOutreach() {
  const [queue, setQueue] = useState<ApprovalItem[] | null>(null);
  const [batches, setBatches] = useState<Batch[] | null>(null);
  const [activity, setActivity] = useState<GmailActivity | null>(null);
  const [report, setReport] = useState<GmailReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const toast = useToast();

  // Refreshes in place: what's on screen stays until the new data arrives.
  const load = useCallback(async () => {
    const [q, b, a, r] = await Promise.all([
      api.outreachApprovalQueue(),
      api.listOutreachBatches(),
      api.gmailActivity(),
      api.gmailReport(),
    ]);
    setQueue(q.items);
    setBatches(b);
    setActivity(a);
    setReport(r);
    setError(null);
  }, []);

  const firstLoad = useCallback(() => {
    setError(null);
    load().catch((err) => setError(err instanceof ApiError ? err.message : "The API didn't answer. Check that it's running, then try again."));
  }, [load]);

  useEffect(() => {
    firstLoad();
  }, [firstLoad]);

  async function syncReplies() {
    setSyncing(true);
    try {
      const { replies_detected } = await api.syncGmailReplies();
      await load();
      toast(replies_detected === 0 ? "No new replies." : `${replies_detected} new ${replies_detected === 1 ? "reply" : "replies"} found.`);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Replies couldn't be checked. Try again.", "error");
    } finally {
      setSyncing(false);
    }
  }

  async function createBatch(name: string, ids: string[]) {
    const batch = await api.createOutreachBatch(name, ids);
    await load();
    toast(`Batch ${batch.name} created with ${batch.count} ${batch.count === 1 ? "draft" : "drafts"}. Nothing has been sent.`);
  }

  async function dispatch(batch: Batch): Promise<string> {
    const result = await api.dispatchOutreachBatch(batch.id);
    await load();
    const failed = result.failed ? `, ${result.failed} failed` : "";
    return `Sent ${result.sent}${failed}. ${result.remaining_daily_capacity} more can go out today.`;
  }

  async function control(batch: Batch, action: BatchAction) {
    await api.controlOutreachBatch(batch.id, action);
    await load();
  }

  const loaded = queue !== null && batches !== null;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Outreach"
        description="Approve drafts, group them into batches, and send within your daily and hourly limits."
        actions={
          <Button variant="outline" onClick={() => void syncReplies()} disabled={syncing || !loaded}>
            {syncing ? "Checking Gmail…" : "Check for replies"}
          </Button>
        }
      />

      {error && <ErrorState title="Outreach didn't load" body={error} onRetry={firstLoad} />}

      {!loaded && !error && (
        <LoadingRegion label="Loading outreach" className="flex flex-col gap-6">
          <Card className="grid grid-cols-2 gap-6 p-5 sm:grid-cols-5">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-7 w-10" />
              </div>
            ))}
          </Card>
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
            <SkeletonRows rows={4} />
            <SkeletonRows rows={3} />
          </div>
        </LoadingRegion>
      )}

      {loaded && (
        <>
          <Card className="p-5">
            <h2 className="sr-only">Totals</h2>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-5">
              <Figure label="Sent" value={report?.sent} />
              <Figure label="Replies" value={report?.replied} />
              <Figure label="Approved" value={report?.approved} />
              <Figure label="Added to batches" value={report?.queued} />
              <Figure label="Failed" value={report?.failed} tone={report?.failed ? "bad" : undefined} />
            </dl>
          </Card>

          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div className="flex min-w-0 flex-col gap-6">
              <ApprovalQueue items={queue} onCreateBatch={createBatch} />
              <BatchList
                batches={batches}
                remainingToday={activity ? Math.max(0, activity.daily_limit - activity.sent_today) : null}
                onDispatch={dispatch}
                onControl={control}
              />
            </div>
            <section aria-labelledby="activity-heading" className="flex flex-col gap-3">
              <h2 id="activity-heading" className="text-base font-semibold text-ink">
                Recent activity
              </h2>
              <ActivityFeed activity={activity} limit={12} />
            </section>
          </div>
        </>
      )}
    </div>
  );
}

function Figure({ label, value, tone }: { label: string; value: number | undefined; tone?: "bad" }) {
  return (
    <div className="min-w-0">
      <dt className="text-[13px] text-graphite">{label}</dt>
      <dd className={tone === "bad" ? "text-[28px] font-medium leading-8 tabular-nums text-brick" : "text-[28px] font-medium leading-8 tabular-nums text-ink"}>
        {value ?? "–"}
      </dd>
    </div>
  );
}

// The demo can read the sample leads but none of the Gmail routes, so the
// queue is built from the prepared drafts and shown read-only.
function DemoOutreach() {
  const [items, setItems] = useState<ApprovalItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    fetchAllBusinesses()
      .then((leads) => Promise.all(leads.slice(0, 12).map((lead) => api.getBusiness(lead.id))))
      .then((details) =>
        setItems(
          details.flatMap((business) => {
            const draft = [...business.outreach_drafts]
              .filter((d) => !d.sent_at)
              .sort((a, b) => b.created_at.localeCompare(a.created_at))[0];
            if (!draft || !business.email) return [];
            return [
              {
                outreach_id: draft.id,
                business_id: business.id,
                business_name: business.name,
                email: business.email,
                subject: draft.subject,
                approval_status: draft.approval_status,
                created_at: draft.created_at,
              },
            ];
          })
        )
      )
      .catch((err) => setError(err instanceof ApiError ? err.message : "The API didn't answer. Check that it's running, then try again."));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <DemoNotice>These are prepared drafts for fictional leads. Approving, batching and sending are turned off, and nothing is ever emailed.</DemoNotice>
      <PageHeader title="Outreach" description="Where drafts are approved, grouped into batches and sent within daily and hourly limits." />

      {error && <ErrorState title="The sample drafts didn't load" body={error} onRetry={load} />}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0">
          {items === null && !error ? (
            <LoadingRegion label="Loading sample drafts">
              <SkeletonRows rows={3} />
            </LoadingRegion>
          ) : (
            items && <ApprovalQueue items={items} demo />
          )}
        </div>
        <Card className="p-5">
          <h2 className="text-base font-semibold text-ink">How sending works</h2>
          <ol className="mt-3 flex flex-col gap-3 text-sm leading-6 text-graphite">
            <li>
              <span className="font-medium text-ink">1. Approve.</span> Someone reads each draft on the lead&apos;s page and approves it.
              Unapproved drafts can&apos;t be batched.
            </li>
            <li>
              <span className="font-medium text-ink">2. Batch.</span> Approved drafts are grouped into a named batch with its own sending
              hours.
            </li>
            <li>
              <span className="font-medium text-ink">3. Send.</span> Pressing Send goes out through Gmail, stopping at the daily and hourly
              limits. Replies are matched back to their leads.
            </li>
          </ol>
          {items && items[0] && (
            <Link
              href={`/prospects/${items[0].business_id}?tab=outreach`}
              className="focus-ring mt-4 inline-block rounded-[2px] text-sm text-survey underline-offset-2 hover:underline"
            >
              Read a sample draft
            </Link>
          )}
        </Card>
      </div>
    </div>
  );
}
