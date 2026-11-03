"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ScoreGrade } from "@/components/lead/score-grade";
import { StageTrack } from "@/components/lead/stage-track";
import { PhaseSummary } from "@/components/pipeline/phase-summary";
import { ActivityFeed, type GmailActivity } from "@/components/outreach/activity-feed";
import { DemoNotice, PageHeader } from "@/components/shell/page-header";
import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { buttonClasses } from "@/components/ui/button";
import { Card, PrimaryCard } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { RadialGauge } from "@/components/ui/gauge";
import { LoadingRegion, Skeleton, SkeletonRows } from "@/components/ui/skeleton";
import { api, API_BASE_URL, ApiError } from "@/lib/api";
import { fetchAllBusinesses } from "@/lib/fetch-all";
import { isDemoMode } from "@/lib/runtime";
import type { BusinessListItem } from "@/lib/types";

type ApprovalItem = Awaited<ReturnType<typeof api.outreachApprovalQueue>>["items"][number];
type GmailReport = Awaited<ReturnType<typeof api.gmailReport>>;

export default function DashboardPage() {
  return isDemoMode ? <DemoLanding /> : <LiveDashboard />;
}

function apiProblem(err: unknown): string {
  // Name the server only when it was configured, or when it's the dev default.
  const where =
    process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NODE_ENV === "development" ? ` at ${API_BASE_URL}` : "";
  if (err instanceof ApiError) return `The API${where} answered with an error (${err.status}): ${err.message}`;
  return `The API${where} isn't responding. Start the backend, then try again.`;
}

function LiveDashboard() {
  const [businesses, setBusinesses] = useState<BusinessListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activity, setActivity] = useState<GmailActivity | null>(null);
  const [activityFailed, setActivityFailed] = useState(false);
  const [queue, setQueue] = useState<ApprovalItem[] | null>(null);
  const [report, setReport] = useState<GmailReport | null>(null);

  const loadLeads = useCallback(() => {
    setError(null);
    fetchAllBusinesses({ sort_by: "created_at", sort_dir: "desc" })
      .then(setBusinesses)
      .catch((err) => setError(apiProblem(err)));
  }, []);

  useEffect(() => {
    loadLeads();
    api.gmailActivity().then(setActivity).catch(() => setActivityFailed(true));
    api.outreachApprovalQueue().then((res) => setQueue(res.items)).catch(() => {});
    api.gmailReport().then(setReport).catch(() => {});
  }, [loadLeads]);

  const stats = useMemo(() => {
    if (!businesses) return null;
    const scored = businesses.filter((b) => b.latest_opportunity_score !== null);
    const avgScore =
      scored.length === 0
        ? null
        : Math.round(scored.reduce((sum, b) => sum + (b.latest_opportunity_score ?? 0), 0) / scored.length);
    return {
      total: businesses.length,
      audited: scored.length,
      strong: scored.filter((b) => (b.latest_opportunity_score ?? 0) >= 70).length,
      avgScore,
      top: [...scored]
        .sort((a, b) => (b.latest_opportunity_score ?? 0) - (a.latest_opportunity_score ?? 0))
        .slice(0, 8),
    };
  }, [businesses]);

  const toReview = queue?.filter((item) => item.approval_status !== "APPROVED").length;
  const readyToSend = queue?.filter((item) => item.approval_status === "APPROVED").length;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Today"
        description="What needs attention across your leads, and where they stand."
        meta={stats ? `${stats.total} leads, ${stats.audited} audited` : undefined}
        actions={
          <Link href="/discover" className={buttonClasses()}>
            Find leads
          </Link>
        }
      />

      {error && <ErrorState title="Your leads didn't load" body={error} onRetry={loadLeads} />}

      <section aria-labelledby="attention-heading" className="grid gap-4 lg:grid-cols-[1fr_auto]">
        <Card className="flex flex-col justify-between gap-6 p-5">
          <h2 id="attention-heading" className="text-base font-semibold text-ink">
            Needs attention
          </h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
            <Figure label="Drafts to review" value={toReview} href="/outreach" />
            <Figure label="Ready to send" value={readyToSend} href="/outreach" />
            <Figure label="Replies" value={report?.replied} href="/outreach" />
            <Figure label="Strong opportunities" value={stats?.strong} href="#opportunities" />
          </dl>
        </Card>
        <Card className="flex items-center gap-5 p-5 lg:w-[440px]">
          <RadialGauge score={stats?.avgScore ?? null} label="Average opportunity" />
          <p className="text-sm leading-6 text-graphite">
            {stats === null
              ? error
                ? "Shown once your leads load."
                : "Averaging the audited leads."
              : stats.avgScore === null
                ? "No lead has been audited yet. Open a lead and run an audit to score it."
                : `Across ${stats.audited} audited ${stats.audited === 1 ? "lead" : "leads"}. Strong starts at 70.`}
          </p>
        </Card>
      </section>

      <section aria-labelledby="pipeline-heading">
        <SectionHeading id="pipeline-heading" title="Pipeline" href="/pipeline" linkLabel="Open pipeline" />
        {businesses ? (
          <PhaseSummary businesses={businesses} />
        ) : error ? (
          <p className="text-sm text-graphite">Shown once your leads load.</p>
        ) : (
          <LoadingRegion label="Counting leads" className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[0, 1, 2, 3, 4].map((i) => (
              <Card key={i} className="space-y-2 p-4">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-6 w-8" />
              </Card>
            ))}
          </LoadingRegion>
        )}
      </section>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <section id="opportunities" aria-labelledby="opportunities-heading" className="min-w-0 scroll-mt-6">
          <SectionHeading id="opportunities-heading" title="Top opportunities" href="/prospects" linkLabel="All leads" />
          {error && !stats ? (
            <p className="text-sm text-graphite">Shown once your leads load.</p>
          ) : (
            <TopOpportunities items={stats?.top ?? null} />
          )}
        </section>

        <section aria-labelledby="activity-heading" className="min-w-0">
          <SectionHeading id="activity-heading" title="Gmail activity" href="/outreach" linkLabel="Outreach" />
          <ActivityFeed activity={activity} unavailable={activityFailed && activity === null} />
        </section>
      </div>
    </div>
  );
}

function SectionHeading({ id, title, href, linkLabel }: { id: string; title: string; href: string; linkLabel: string }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-4">
      <h2 id={id} className="text-base font-semibold text-ink">
        {title}
      </h2>
      <Link href={href} className="focus-ring rounded-tag text-[13px] text-survey hover:underline">
        {linkLabel}
      </Link>
    </div>
  );
}

function Figure({ label, value, href }: { label: string; value: number | undefined; href: string }) {
  return (
    <div className="min-w-0">
      <dt className="sr-only">{label}</dt>
      <dd>
        <Link href={href} className="focus-ring group -m-1 flex flex-col rounded-control p-1">
          <span className="text-[28px] font-medium leading-8 tabular-nums text-ink group-hover:text-survey">
            {value ?? "–"}
          </span>
          <span className="mt-1 text-[13px] text-graphite group-hover:text-ink" aria-hidden="true">
            {label}
          </span>
        </Link>
      </dd>
    </div>
  );
}

function TopOpportunities({ items }: { items: BusinessListItem[] | null }) {
  if (items === null) {
    return (
      <LoadingRegion label="Loading leads">
        <SkeletonRows rows={5} />
      </LoadingRegion>
    );
  }
  if (items.length === 0) {
    return (
      <EmptyState
        title="No audited leads yet"
        body="An audit scores a lead's website from 0 to 100. Find some leads, then run an audit from a lead's page."
        action={
          <Link href="/discover" className={buttonClasses("outline", "sm")}>
            Find leads
          </Link>
        }
      />
    );
  }
  return (
    <div className="data-table">
      <table className="text-sm">
        <thead>
          <tr>
            <th scope="col" className="w-1/2">Business</th>
            <th scope="col" className="hidden md:table-cell">Quality</th>
            <th scope="col">Opportunity</th>
            <th scope="col" className="hidden sm:table-cell">Stage</th>
          </tr>
        </thead>
        <tbody>
          {items.map((b) => (
            <tr key={b.id}>
              <td className="max-w-0 py-2">
                <Link href={`/prospects/${b.id}`} className="focus-ring block truncate rounded-tag font-medium text-ink hover:underline">
                  {b.name}
                </Link>
                <span className="block truncate text-xs text-graphite">
                  {[b.category, b.city].filter(Boolean).join(", ") || "No category or city"}
                </span>
              </td>
              <td className="hidden md:table-cell">
                <QualityBadge category={b.latest_quality_category} />
              </td>
              <td className="whitespace-nowrap">
                <OpportunityScoreBadge score={b.latest_opportunity_score} />
              </td>
              <td className="hidden sm:table-cell">
                <StatusBadge status={b.current_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DemoLanding() {
  const [sample, setSample] = useState<BusinessListItem | null | undefined>(undefined);

  useEffect(() => {
    api
      .listBusinesses({ limit: 200 })
      .then((res) => {
        const scored = res.items.filter((b) => b.latest_opportunity_score !== null);
        scored.sort((a, b) => (b.latest_opportunity_score ?? 0) - (a.latest_opportunity_score ?? 0));
        setSample(scored[0] ?? res.items[0] ?? null);
      })
      .catch(() => setSample(null));
  }, []);

  return (
    <div className="flex flex-col gap-10">
      <DemoNotice>
        This is a working internal tool, shown here with fictional sample businesses. Nothing you do sends email or
        touches a real website.
      </DemoNotice>

      <div className="grid items-start gap-10 lg:grid-cols-[minmax(0,1fr)_420px] lg:gap-14">
        <section className="max-w-xl pt-2">
          <h1 className="font-serif text-[34px] font-medium leading-[40px] tracking-[-0.015em] text-ink sm:text-[44px] sm:leading-[50px]">
            Find the local businesses a better website would help most.
          </h1>
          <div className="mt-6 flex flex-col gap-3 text-[15px] leading-7 text-graphite">
            <p>ProspectOS finds local businesses and audits their websites.</p>
            <p>Each one gets an opportunity score, listed with the findings that produced it.</p>
            <p>Outreach is drafted from those findings, and nothing is sent until a person approves it.</p>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/prospects" className={buttonClasses()}>
              Browse sample leads
            </Link>
            <Link href="/pipeline" className={buttonClasses("outline")}>
              See the pipeline
            </Link>
          </div>
        </section>

        <SampleLead sample={sample} />
      </div>

      <DemoSteps sample={sample} />
    </div>
  );
}

// The demo's best path, in order. Links point at the highest-scoring sample
// once it has loaded, and at the leads list until then.
function DemoSteps({ sample }: { sample: BusinessListItem | null | undefined }) {
  const lead = sample ? `/prospects/${sample.id}` : "/prospects";
  const steps = [
    {
      title: "Open a sample lead",
      body: "See the business's details, its opportunity score and the recommended approach.",
      href: lead,
      link: sample ? `Open ${sample.name}` : "Browse sample leads",
    },
    {
      title: "Replay its audit",
      body: "Press Replay audit on the lead's page. The score counts up and every finding behind it is listed.",
    },
    {
      title: "Read the drafted outreach",
      body: "The email is written from the audit's findings. In the real tool it waits here until a person approves it.",
      href: sample ? `${lead}?tab=outreach` : "/outreach",
      link: "Read the draft",
    },
  ];

  return (
    <section aria-labelledby="demo-steps-heading" className="border-t border-rule pt-8">
      <h2 id="demo-steps-heading" className="text-base font-semibold text-ink">
        Try it in three steps
      </h2>
      <ol className="mt-5 grid gap-6 sm:grid-cols-3">
        {steps.map((step, i) => (
          <li key={step.title} className="flex gap-3">
            <span
              aria-hidden="true"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-survey/40 font-serif text-[13px] tabular-nums text-survey"
            >
              {i + 1}
            </span>
            <div className="flex flex-col gap-1.5">
              <h3 className="text-sm font-medium text-ink">{step.title}</h3>
              <p className="max-w-prose text-[13px] leading-5 text-graphite">{step.body}</p>
              {step.href && (
                <Link href={step.href} className="focus-ring w-fit rounded-tag text-[13px] font-medium text-survey hover:underline">
                  {step.link}
                </Link>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function SampleLead({ sample }: { sample: BusinessListItem | null | undefined }) {
  if (sample === undefined) {
    return (
      <LoadingRegion label="Loading a sample lead">
        <Card className="flex h-[300px] flex-col gap-4 p-6">
          <Skeleton className="h-6 w-1/2" />
          <Skeleton className="h-3.5 w-1/3" />
          <Skeleton className="mt-4 h-16 w-24" />
          <Skeleton className="mt-auto h-3 w-full" />
        </Card>
      </LoadingRegion>
    );
  }
  if (sample === null) {
    return (
      <Card className="p-6 text-sm text-graphite">
        The sample data isn&apos;t available right now.{" "}
        <Link href="/prospects" className="focus-ring rounded-tag text-survey hover:underline">
          Open the leads list
        </Link>{" "}
        to try again.
      </Card>
    );
  }
  const where = [sample.category, sample.city].filter(Boolean).join(", ");
  return (
    <PrimaryCard className="flex flex-col gap-6 p-6">
      <div>
        <p className="text-xs text-graphite">Highest-scoring sample lead</p>
        <h2 className="mt-1.5 font-serif text-[22px] font-medium leading-7 text-ink">{sample.name}</h2>
        {where && <p className="mt-1 text-[13px] text-graphite">{where}</p>}
      </div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <ScoreGrade score={sample.latest_opportunity_score} label="Opportunity" />
        {sample.latest_quality_category && (
          <div className="flex flex-col items-start gap-1.5">
            <span className="text-xs text-graphite">Website quality</span>
            <QualityBadge category={sample.latest_quality_category} />
          </div>
        )}
      </div>
      <StageTrack status={sample.current_status} />
      <Link href={`/prospects/${sample.id}`} className={buttonClasses("outline", "md", "self-start")}>
        Open this lead
      </Link>
    </PrimaryCard>
  );
}
