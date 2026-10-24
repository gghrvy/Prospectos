"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, PrimaryCard } from "@/components/ui/card";
import { RadialGauge } from "@/components/ui/gauge";
import { api, ApiError } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";
import type { BusinessListItem } from "@/lib/types";

export default function DashboardPage() {
  const [businesses, setBusinesses] = useState<BusinessListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gmailActivity, setGmailActivity] = useState<{ sent_today: number; daily_limit: number; items: { id: string; outreach_id: string | null; business_id: string | null; action: string; detail: string | null; created_at: string }[] } | null>(null);
  const [approvalQueue, setApprovalQueue] = useState<{ outreach_id: string; business_id: string; business_name: string; email: string; subject: string | null; approval_status: string; created_at: string }[]>([]);
  const [batches, setBatches] = useState<{ id: string; name: string; status: string; created_at: string; count: number; timezone: string }[]>([]);
  const [selectedDrafts, setSelectedDrafts] = useState<Set<string>>(new Set());
  const [batchName, setBatchName] = useState("");
  const [batchBusy, setBatchBusy] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [report, setReport] = useState<{ sent: number; failed: number; replied: number; approved: number; queued: number; POSITIVE_REPLY: number; MEETING: number; PROPOSAL: number; WON: number } | null>(null);
  const [syncingReplies, setSyncingReplies] = useState(false);

  useEffect(() => {
    if (isDemoMode) return;
    api
      .listBusinesses({ limit: 200, sort_by: "created_at", sort_dir: "desc" })
      .then((res) => setBusinesses(res.items))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to reach the backend API."));
    api.gmailActivity().then(setGmailActivity).catch(() => {});
    api.outreachApprovalQueue().then((res) => setApprovalQueue(res.items)).catch(() => {});
    api.listOutreachBatches().then(setBatches).catch(() => {});
    api.gmailReport().then(setReport).catch(() => {});
  }, []);

  if (isDemoMode) {
    return (
      <div className="flex flex-col gap-6">
        <div className="rounded-lg border border-signal/40 bg-signal/10 px-4 py-3">
          <p className="font-mono text-xs font-medium uppercase tracking-wider text-signal">Demo mode</p>
          <p className="mt-1 text-sm text-foreground">Explore prepared fictional businesses and their evidence-based audits. No real emails, external accounts, or websites are affected.</p>
        </div>
        <div>
          <p className="page-kicker text-signal">ProspectOS demonstration</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Find the next best digital opportunity.</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">Choose a sample business to inspect its website findings, evidence, Prospect Fit, conversion opportunities, recommendations, and a safe outreach preview.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {["Dental clinic", "Restaurant", "Real estate agency", "Home services"].map((label) => <Link key={label} href="/prospects" className="rounded-lg border border-border bg-panel p-4 text-sm font-medium transition-colors hover:border-signal/50 hover:text-signal">{label}<span className="mt-1 block text-xs font-normal text-muted-foreground">Prepared sample audit</span></Link>)}
        </div>
        <Link href="/prospects" className="w-fit rounded-md bg-signal px-4 py-2 text-sm font-medium text-slate-950">Explore sample businesses</Link>
      </div>
    );
  }

  const stats = useMemo(() => {
    if (!businesses) return null;
    const total = businesses.length;
    const noWebsite = businesses.filter((b) => b.website_status === "not_found" || !b.website).length;
    const highOpportunity = businesses.filter((b) => (b.latest_opportunity_score ?? 0) >= 70).length;
    const audited = businesses.filter((b) => b.latest_opportunity_score !== null).length;
    const won = businesses.filter((b) => b.current_status === "WON").length;
    const scored = businesses.filter((b) => b.latest_opportunity_score !== null);
    const avgScore =
      scored.length === 0
        ? null
        : Math.round(scored.reduce((sum, b) => sum + (b.latest_opportunity_score ?? 0), 0) / scored.length);
    return { total, noWebsite, highOpportunity, audited, won, avgScore };
  }, [businesses]);

  const topOpportunities = useMemo(() => {
    if (!businesses) return [];
    return [...businesses]
      .filter((b) => b.latest_opportunity_score !== null)
      .sort((a, b) => (b.latest_opportunity_score ?? 0) - (a.latest_opportunity_score ?? 0))
      .slice(0, 8);
  }, [businesses]);

  const approvalGroups = useMemo(() => {
    const groups = new Map<string, typeof approvalQueue>();
    approvalQueue.forEach((item) => groups.set(item.business_id, [...(groups.get(item.business_id) ?? []), item]));
    return [...groups.values()];
  }, [approvalQueue]);

  const pipeline = useMemo(() => {
    const stages = ["NEW", "QUALIFIED", "CONTACTED", "REPLIED", "WON"];
    return stages.map((stage) => ({ stage, count: businesses?.filter((business) => business.current_status === stage).length ?? 0 }));
  }, [businesses]);

  return (
    <div className="flex flex-col gap-6">
      {isDemoMode && (
        <div className="rounded-lg border border-signal/40 bg-signal/10 px-4 py-3">
          <p className="font-mono text-xs font-medium uppercase tracking-wider text-signal">Demo mode</p>
          <p className="mt-1 text-sm text-foreground">Explore prepared fictional businesses and their evidence-based audits. No real emails, external accounts, or websites are affected.</p>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-wider text-signal">Live signal</p>
          <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Find, audit, and track local business prospects.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/discover">
            <Button variant="outline">Discover prospects</Button>
          </Link>
          <Link href="/outreach">
            <Button variant="outline">Open outreach</Button>
          </Link>
          <Link href="/prospects">
            <Button>View all prospects</Button>
          </Link>
        </div>
      </div>

      {error && (
        <Card className="border-red-500/40 bg-red-500/5">
          <CardContent className="text-sm text-red-400">
            Couldn&apos;t reach the backend API: {error}. Is it running at{" "}
            <code>{process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}</code>?
          </CardContent>
        </Card>
      )}

      <section className="grid gap-6 border-y border-border/70 py-6 lg:grid-cols-[1.4fr_.6fr]">
        <div>
          <p className="page-kicker text-signal">Today</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">Here&apos;s what needs attention.</h2>
          <div className="mt-5 grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4">
            <Attention label="Drafts to review" value={approvalQueue.filter((item) => item.approval_status !== "APPROVED").length} href="#approval-queue" />
            <Attention label="Ready to send" value={approvalQueue.filter((item) => item.approval_status === "APPROVED").length} href="#approval-queue" />
            <Attention label="Reply signals" value={report?.replied ?? 0} href="#activity" />
            <Attention label="High opportunity" value={stats?.highOpportunity} href="#opportunities" />
          </div>
        </div>
        <div className="flex items-center gap-5 border-t border-border/70 pt-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0"><RadialGauge score={stats?.avgScore ?? null} label="Average opportunity" /><p className="text-sm text-muted-foreground">Your audited pipeline is averaging <span className="font-medium text-foreground">{stats?.avgScore ?? "—"}</span> opportunity points.</p></div>
      </section>

      <section className="border-b border-border/70 pb-5"><div className="flex items-center justify-between"><div><p className="page-kicker">Pipeline</p><h2 className="mt-1 text-base font-semibold">Where prospects are moving</h2></div><Link href="/prospects" className="text-sm text-signal hover:underline">View pipeline</Link></div><div className="mt-4 grid grid-cols-5 gap-2">{pipeline.map(({ stage, count }) => <div key={stage} className="border-l border-border pl-3 first:border-l-0 first:pl-0"><p className="font-mono text-xl font-semibold">{count}</p><p className="mt-1 text-xs text-muted-foreground">{stage.charAt(0) + stage.slice(1).toLowerCase()}</p></div>)}</div></section>

      <Card id="approval-queue" className="hidden">
        <CardHeader><CardTitle>Approval queue</CardTitle></CardHeader>
        <CardContent>
          {!approvalQueue.length ? <p className="text-sm text-muted-foreground">No unsent drafts with a prospect email.</p> : <>
            <div className="flex flex-col gap-2">
              {approvalGroups.slice(0, 20).map((group) => { const item = group[0]; const approved = group.filter((draft) => draft.approval_status === "APPROVED"); return <div key={item.business_id} className="flex items-start gap-3 border-t border-border pt-3 text-sm">
                <input type="checkbox" disabled={!approved.length} checked={approved.length > 0 && approved.every((draft) => selectedDrafts.has(draft.outreach_id))} onChange={() => setSelectedDrafts((previous) => { const next = new Set(previous); approved.forEach((draft) => next.has(draft.outreach_id) ? next.delete(draft.outreach_id) : next.add(draft.outreach_id)); return next; })} aria-label={`Select ${item.business_name}`} />
                <Link href={`/prospects/${item.business_id}`} className="min-w-0 flex-1 hover:underline"><strong>{item.business_name}</strong><p className="mt-0.5 truncate text-xs text-muted-foreground">{item.subject ?? "No subject"} · {item.email}</p>{group.length > 1 && <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{group.length} drafts awaiting review</p>}</Link>
                <span className={approved.length === group.length ? "text-emerald-400" : "text-amber-400"}>{approved.length === group.length ? "Approved" : "Needs review"}</span>
              </div>})}
            </div>
            <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-border pt-3">
              <label className="flex flex-col gap-1 text-xs text-muted-foreground">Batch name<input className="h-9 rounded-md border border-border bg-transparent px-2 text-sm text-foreground" value={batchName} onChange={(e) => setBatchName(e.target.value)} placeholder="e.g. Austin retailers — Aug 23" /></label>
              <Button disabled={batchBusy || selectedDrafts.size === 0 || !batchName.trim()} onClick={async () => { setBatchBusy(true); setBatchError(null); try { await api.createOutreachBatch(batchName, [...selectedDrafts]); setBatchName(""); setSelectedDrafts(new Set()); const [queue, nextBatches] = await Promise.all([api.outreachApprovalQueue(), api.listOutreachBatches()]); setApprovalQueue(queue.items); setBatches(nextBatches); } catch (err) { setBatchError(err instanceof ApiError ? err.message : "Could not create batch."); } finally { setBatchBusy(false); } }}>{batchBusy ? "Creating…" : `Create batch (${selectedDrafts.size})`}</Button>
              {batchError && <span className="text-xs text-red-400">{batchError}</span>}
            </div>
          </>}
        </CardContent>
      </Card>

      <Card className="hidden">
        <CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Outreach results</CardTitle><Button size="sm" variant="outline" disabled={syncingReplies} onClick={async () => { setSyncingReplies(true); try { await api.syncGmailReplies(); const [nextReport, activity] = await Promise.all([api.gmailReport(), api.gmailActivity()]); setReport(nextReport); setGmailActivity(activity); } finally { setSyncingReplies(false); } }}>{syncingReplies ? "Syncing…" : "Sync replies"}</Button></CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
          {[["Sent", report?.sent], ["Replies", report?.replied], ["Approved", report?.approved], ["Queued", report?.queued], ["Failed", report?.failed]].map(([label, value]) => <div key={String(label)}><p className="text-muted-foreground">{label}</p><p className="font-mono text-xl">{value ?? "—"}</p></div>)}
        </CardContent>
      </Card>

      <Card className="hidden">
        <CardHeader><CardTitle>Batch outreach</CardTitle></CardHeader>
        <CardContent>
          {!batches.length ? <p className="text-sm text-muted-foreground">No named batches yet. Approve drafts, then create a batch from the approval queue.</p> :
            <div className="flex flex-col gap-2">{batches.map((batch) => <div key={batch.id} className="flex items-center justify-between border-t border-border pt-2 text-sm">
              <span><strong>{batch.name}</strong><span className="text-muted-foreground"> · {batch.count} drafts · {batch.status} · {batch.timezone}</span></span>
              <span className="flex gap-1"><Button size="sm" variant="outline" onClick={async () => { await api.dispatchOutreachBatch(batch.id); location.reload(); }}>Dispatch now</Button>{batch.status === "ACTIVE" ? <Button size="sm" variant="outline" onClick={async () => { await api.controlOutreachBatch(batch.id, "pause"); location.reload(); }}>Pause</Button> : <Button size="sm" variant="outline" onClick={async () => { await api.controlOutreachBatch(batch.id, "resume"); location.reload(); }}>Resume</Button>}<Button size="sm" variant="destructive" onClick={async () => { if (confirm(`Cancel "${batch.name}"? Unsent drafts will be removed from the batch.`)) { await api.controlOutreachBatch(batch.id, "cancel"); location.reload(); } }}>Cancel</Button></span>
            </div>)}</div>}
        </CardContent>
      </Card>

      <Card id="activity" className="border-x-0 border-b-0 border-t-0 rounded-none bg-transparent">
        <CardHeader>
          <CardTitle>Gmail activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-3 text-xs text-muted-foreground">Daily guardrail: {gmailActivity?.sent_today ?? 0} / {gmailActivity?.daily_limit ?? 10} sent. Batch sending will use this same limit.</p>
          {!gmailActivity?.items.length ? <p className="text-sm text-muted-foreground">No Gmail actions yet.</p> : (
            <div className="flex flex-col gap-2">{gmailActivity.items.slice(0, 8).map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-4 border-t border-border pt-2 text-sm">
                <span><span className={activityTone(item.action)}>{activityLabel(item.action)}</span>{item.detail ? `: ${item.detail}` : ""}</span>
                <span className="shrink-0 text-xs text-muted-foreground">{new Date(item.created_at).toLocaleString()}</span>
              </div>
            ))}</div>
          )}
        </CardContent>
      </Card>

      <Card id="opportunities">
        <CardHeader>
          <CardTitle>Top opportunities</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {businesses === null ? (
            <p className="p-4 text-sm text-muted-foreground">Loading…</p>
          ) : topOpportunities.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              No audited prospects yet. Head to{" "}
              <Link href="/discover" className="underline">
                Discover
              </Link>{" "}
              to find some, then run an audit from their detail page.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-t border-border text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-2 font-medium">Business</th>
                  <th className="px-4 py-2 font-medium">Category</th>
                  <th className="px-4 py-2 font-medium">Quality</th>
                  <th className="px-4 py-2 font-medium">Opportunity</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {topOpportunities.map((b) => (
                  <tr key={b.id} className="bracket-hover border-t border-border hover:bg-white/5">
                    <td className="px-4 py-2">
                      <Link href={`/prospects/${b.id}`} className="font-medium hover:underline">
                        {b.name}
                      </Link>
                      <div className="text-xs text-muted-foreground">{b.city ?? "—"}</div>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">{b.category ?? "—"}</td>
                    <td className="px-4 py-2">
                      <QualityBadge category={b.latest_quality_category} />
                    </td>
                    <td className="px-4 py-2">
                      <OpportunityScoreBadge score={b.latest_opportunity_score} />
                    </td>
                    <td className="px-4 py-2">
                      <StatusBadge status={b.current_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Attention({
  label,
  value,
  highlight = false,
  href,
}: {
  label: string;
  value: number | undefined;
  highlight?: boolean;
  href: string;
}) {
  return (
    <Link href={href} className="group border-l border-border pl-4 first:border-l-0 first:pl-0">
      <span className={`font-mono text-3xl font-semibold tabular-nums tracking-tight group-hover:text-signal ${highlight ? "text-signal" : ""}`}>{value === undefined ? "—" : value}</span>
      <span className="mt-1 block text-xs text-muted-foreground group-hover:text-foreground">{label}</span>
    </Link>
  );
}

function activityLabel(action: string) {
  return ({ SENT: "Email sent", SEND_FAILED: "Send failed", REPLIED: "Reply received", APPROVED: "Draft approved", QUEUED: "Queued for sending" } as Record<string, string>)[action] ?? action.replace(/_/g, " ");
}

function activityTone(action: string) {
  if (action === "SENT" || action === "REPLIED" || action === "APPROVED") return "text-emerald-400";
  if (action === "SEND_FAILED") return "text-red-400";
  return "text-amber-400";
}
