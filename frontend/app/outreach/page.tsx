"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";

type QueueItem = { outreach_id: string; business_id: string; business_name: string; email: string; subject: string | null; approval_status: string };

export default function OutreachPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [activity, setActivity] = useState<{ action: string; detail: string | null; created_at: string; id: string }[]>([]);
  const [report, setReport] = useState<{ sent: number; failed: number; replied: number; approved: number; queued: number } | null>(null);
  const [selected, setSelected] = useState(new Set<string>());
  const [name, setName] = useState("");
  const load = () => Promise.all([api.outreachApprovalQueue(), api.gmailActivity(), api.gmailReport()]).then(([q, a, r]) => { setQueue(q.items); setActivity(a.items); setReport(r); });

  useEffect(() => { if (!isDemoMode) load().catch(() => {}); }, []);

  if (isDemoMode) return <div className="flex max-w-2xl flex-col gap-4 rounded-lg border border-signal/40 bg-signal/10 p-6"><p className="font-mono text-xs font-medium uppercase tracking-wider text-signal">Demo mode</p><h1 className="text-2xl font-semibold tracking-tight">Outreach previews, never delivery.</h1><p className="text-sm text-muted-foreground">Prepared prospects include fictional outreach previews. Gmail, approval queues, batches, reply sync, and sending are intentionally unavailable in this public demo.</p><Link href="/prospects" className="text-sm font-medium text-signal hover:underline">Open a sample prospect to view a draft preview</Link></div>;

  return <div className="flex flex-col gap-7"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="page-kicker text-signal">Outreach workspace</p><h1 className="text-3xl font-semibold tracking-tight">Review, send, and follow up.</h1><p className="mt-1 text-sm text-muted-foreground">Keep the delivery workflow separate from prospect research.</p></div><Button variant="outline" onClick={async () => { await api.syncGmailReplies(); await load(); }}>Sync replies</Button></header><section className="grid grid-cols-2 gap-5 border-y border-border/70 py-5 sm:grid-cols-5">{[["Sent", report?.sent], ["Replies", report?.replied], ["Approved", report?.approved], ["Queued", report?.queued], ["Failed", report?.failed]].map(([label, value]) => <div key={String(label)}><p className="font-mono text-2xl font-semibold">{value ?? "—"}</p><p className="text-xs text-muted-foreground">{label}</p></div>)}</section><div className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_360px]"><section><div className="mb-3 flex items-center justify-between"><div><p className="section-heading">Approval queue</p><p className="text-sm text-muted-foreground">The latest actionable draft for each prospect.</p></div><span className="font-mono text-xs text-muted-foreground">{queue.length} prospects</span></div><div className="divide-y divide-border/70 border-y border-border/70">{queue.length ? queue.map((item) => <div key={item.outreach_id} className="flex items-center gap-3 py-3"><input type="checkbox" disabled={item.approval_status !== "APPROVED"} checked={selected.has(item.outreach_id)} onChange={() => setSelected((old) => { const next = new Set(old); next.has(item.outreach_id) ? next.delete(item.outreach_id) : next.add(item.outreach_id); return next; })}/><Link href={`/prospects/${item.business_id}`} className="min-w-0 flex-1"><p className="font-medium">{item.business_name}</p><p className="truncate text-xs text-muted-foreground">{item.subject ?? "No subject"} · {item.email}</p></Link><span className={item.approval_status === "APPROVED" ? "text-xs text-emerald-400" : "text-xs text-amber-400"}>{item.approval_status === "APPROVED" ? "Ready" : "Needs review"}</span></div>) : <p className="py-8 text-sm text-muted-foreground">No drafts need attention.</p>}</div>{selected.size > 0 && <div className="mt-4 flex flex-wrap gap-2"><Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Batch name" className="max-w-xs"/><Button disabled={!name.trim()} onClick={async () => { await api.createOutreachBatch(name, [...selected]); setName(""); setSelected(new Set()); await load(); }}>Create batch ({selected.size})</Button></div>}</section><aside className="border-l border-border/70 pl-0 lg:pl-6"><p className="section-heading">Recent activity</p><div className="mt-3 divide-y divide-border/70">{activity.slice(0, 10).map((item) => <div key={item.id} className="py-3"><p className="text-sm font-medium">{item.action.replace(/_/g, " ")}</p><p className="mt-1 text-xs text-muted-foreground">{item.detail}</p><p className="mt-1 font-mono text-[10px] text-muted-foreground">{new Date(item.created_at).toLocaleString()}</p></div>)}</div></aside></div></div>;
}
