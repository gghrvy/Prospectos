"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PhaseColumn } from "@/components/pipeline/phase-column";
import { DemoNotice, PageHeader } from "@/components/shell/page-header";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingRegion, Skeleton, SkeletonRows } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { fetchAllBusinesses } from "@/lib/fetch-all";
import { isDemoMode } from "@/lib/runtime";
import { PHASES, phaseOf, stageLabel, type Phase } from "@/lib/stages";
import type { BusinessListItem, LeadStatus } from "@/lib/types";

export default function PipelinePage() {
  const [leads, setLeads] = useState<BusinessListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const load = useCallback(() => {
    setError(null);
    fetchAllBusinesses()
      .then(setLeads)
      .catch((err) => setError(err instanceof ApiError ? err.message : "The API didn't answer. Check that it's running, then try again."));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Dashboard links point at /pipeline#<phase>; the columns only exist once
  // the leads arrive, so scroll to the anchor after the first render with data.
  const loaded = leads !== null;
  useEffect(() => {
    if (!loaded || !window.location.hash) return;
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: "start" });
  }, [loaded]);

  async function move(id: string, status: LeadStatus) {
    try {
      await api.changeStatus(id, { status });
      const name = leads?.find((lead) => lead.id === id)?.name ?? "Lead";
      setLeads((current) => (current ?? []).map((lead) => (lead.id === id ? { ...lead, current_status: status } : lead)));
      // The row remounts in its new column, which drops focus to <body>; put
      // it back on the same lead's move button once the new row exists.
      requestAnimationFrame(() =>
        document.querySelector<HTMLElement>(`[aria-label="${CSS.escape(`Move ${name}`)}"]`)?.focus()
      );
      toast(`${name} moved to ${stageLabel(status)}.`);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "The lead couldn't be moved. Try again.", "error");
    }
  }

  const byPhase = Object.fromEntries(PHASES.map((phase) => [phase.id, [] as BusinessListItem[]])) as Record<
    Phase,
    BusinessListItem[]
  >;
  for (const lead of leads ?? []) byPhase[phaseOf(lead.current_status)].push(lead);

  return (
    <div className="flex flex-col gap-6">
      <DemoNotice>The leads below are fictional samples. Moving leads between stages is turned off in the demo.</DemoNotice>

      <PageHeader
        title="Pipeline"
        meta={leads ? `${leads.length} ${leads.length === 1 ? "lead" : "leads"} across five phases` : undefined}
        actions={
          !isDemoMode && (
            <Link href="/discover" className={buttonClasses("outline")}>
              Find leads
            </Link>
          )
        }
      />

      {error && <ErrorState title="The pipeline didn't load" body={error} onRetry={load} />}

      {!leads && !error && (
        <LoadingRegion label="Loading pipeline" className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {PHASES.map((phase, i) => (
            <div key={phase.id} className="rounded-panel border border-rule bg-sheet">
              <div className="space-y-2 border-b border-rule px-4 py-3">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-3 w-32" />
              </div>
              <SkeletonRows rows={i === 0 ? 4 : 2} className="rounded-none border-0" />
            </div>
          ))}
        </LoadingRegion>
      )}

      {leads && leads.length === 0 && (
        <EmptyState
          title="No leads in the pipeline"
          body={
            isDemoMode
              ? "The sample leads aren't available right now."
              : "Every lead you find, import or add starts here in Research and moves right as you contact it."
          }
          action={
            !isDemoMode && (
              <Link href="/discover" className={buttonClasses("outline", "sm")}>
                Find leads
              </Link>
            )
          }
        />
      )}

      {leads && leads.length > 0 && (
        <div className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {PHASES.map((phase) => (
            <PhaseColumn key={phase.id} phase={phase.id} leads={byPhase[phase.id]} demo={isDemoMode} onMove={move} />
          ))}
        </div>
      )}
    </div>
  );
}
