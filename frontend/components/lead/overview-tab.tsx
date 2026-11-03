"use client";

import type { ReactNode } from "react";

import { QualityBadge, SignalMeter } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, PrimaryCard } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Textarea } from "@/components/ui/textarea";
import { OPPORTUNITY_TYPE_LABELS, type BusinessDetail, type WebsiteAudit } from "@/lib/types";
import { hostOf } from "@/lib/utils";

const linkClasses = "focus-ring rounded-[2px] text-survey underline-offset-2 hover:underline";

export function OverviewTab({
  business,
  onShowAudit,
  onRunAudit,
  auditing,
  visualBrief,
  generatingBrief,
  onGenerateBrief,
}: {
  business: BusinessDetail;
  onShowAudit: () => void;
  onRunAudit: () => void;
  auditing: boolean;
  visualBrief: string | null;
  generatingBrief: boolean;
  onGenerateBrief: () => void;
}) {
  const audit = business.latest_audit;
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-w-0 flex-col gap-6">
        {audit ? (
          <>
            <RecommendedApproach
              audit={audit}
              visualBrief={visualBrief}
              generating={generatingBrief}
              onGenerateBrief={onGenerateBrief}
            />
            {audit.audit_summary && (
              <Card>
                <CardHeader>
                  <CardTitle>What the audit found</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <p className="max-w-prose text-sm leading-6 text-ink">{audit.audit_summary}</p>
                  <button type="button" onClick={onShowAudit} className={`${linkClasses} w-fit text-sm`}>
                    See the full audit
                  </button>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <EmptyState
            title="No audit yet"
            body="Run an audit to score this lead. It reads up to 10 pages of the website and explains every point of the score."
            action={
              <Button variant="outline" onClick={onRunAudit} disabled={auditing}>
                {auditing ? "Auditing…" : "Run audit"}
              </Button>
            }
          />
        )}
      </div>

      <aside className="flex flex-col gap-6">
        <ContactDetails business={business} />
        {audit && <ScoreSummary audit={audit} />}
      </aside>
    </div>
  );
}

function RecommendedApproach({
  audit,
  visualBrief,
  generating,
  onGenerateBrief,
}: {
  audit: WebsiteAudit;
  visualBrief: string | null;
  generating: boolean;
  onGenerateBrief: () => void;
}) {
  const items = audit.opportunity_assessments ?? [];
  const primary = items.find((item) => item.classification === "PRIMARY");
  const secondary = items.filter((item) => item.classification === "SECONDARY");
  const rejected = items.filter((item) => item.classification === "REJECTED");
  const typeLabel = (type: string) => OPPORTUNITY_TYPE_LABELS[type] ?? type;

  return (
    <PrimaryCard>
      <CardHeader>
        <CardTitle>Recommended approach</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {primary ? (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <p className="font-serif text-xl font-medium text-ink">{typeLabel(primary.opportunity_type)}</p>
              <p className="text-[13px] tabular-nums text-graphite">
                Recommendation {primary.recommendation_score} of 100, confidence {primary.evidence_confidence}
              </p>
            </div>
            <p className="max-w-prose text-sm leading-6 text-ink">{primary.reasoning}</p>
            <div className="border-l-2 border-rule pl-3">
              <p className="text-xs text-graphite">Evidence</p>
              <p className="mt-0.5 max-w-prose text-sm leading-6 text-ink">{primary.evidence}</p>
            </div>
          </div>
        ) : (
          <p className="max-w-prose text-sm leading-6 text-graphite">
            No angle had strong enough evidence to recommend. You can still pick one by hand on the Outreach tab.
          </p>
        )}

        {(secondary.length > 0 || rejected.length > 0) && (
          <dl className="grid gap-4 sm:grid-cols-2">
            {secondary.length > 0 && (
              <OpportunityList title="Also worth raising" items={secondary.map((i) => [typeLabel(i.opportunity_type), i.recommendation_score])} />
            )}
            {rejected.length > 0 && (
              <OpportunityList title="Not recommended" muted items={rejected.map((i) => [typeLabel(i.opportunity_type), i.recommendation_score])} />
            )}
          </dl>
        )}

        {primary && (
          <div className="flex flex-col gap-3 border-t border-rule pt-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-graphite">A one-page brief for designing a concept around this angle.</p>
              <div className="flex gap-2">
                {visualBrief && (
                  <Button size="sm" variant="ghost" onClick={() => navigator.clipboard.writeText(visualBrief)}>
                    Copy brief
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={onGenerateBrief} disabled={generating}>
                  {generating ? "Writing brief…" : visualBrief ? "Write again" : "Write visual brief"}
                </Button>
              </div>
            </div>
            {visualBrief && (
              <Textarea readOnly value={visualBrief} rows={14} aria-label="Visual brief" className="text-[13px] leading-6" />
            )}
          </div>
        )}
      </CardContent>
    </PrimaryCard>
  );
}

function OpportunityList({ title, items, muted }: { title: string; items: [string, number][]; muted?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-graphite">{title}</dt>
      <dd className="mt-1.5">
        <ul className="flex flex-col gap-1">
          {items.map(([label, score]) => (
            <li key={label} className="flex justify-between gap-3 text-sm">
              <span className={muted ? "text-graphite" : "text-ink"}>{label}</span>
              <span className="tabular-nums text-graphite">{score}</span>
            </li>
          ))}
        </ul>
      </dd>
    </div>
  );
}

function ContactDetails({ business }: { business: BusinessDetail }) {
  const rows: [string, ReactNode][] = [
    [
      "Website",
      business.website ? (
        <a href={business.website} target="_blank" rel="noreferrer" className={linkClasses}>
          {hostOf(business.website)}
        </a>
      ) : (
        <span className="text-graphite">Website not found from available sources.</span>
      ),
    ],
  ];
  if (!business.website && business.social_url) {
    rows.push([
      "Social",
      <span key="social" className="flex flex-col gap-0.5">
        <a href={business.social_url} target="_blank" rel="noreferrer" className={linkClasses}>
          {business.social_url.includes("instagram.com") ? "Instagram page" : "Facebook page"}
        </a>
        <span className="text-xs text-graphite">Message them there by hand; email can&apos;t reach them.</span>
      </span>,
    ]);
  }
  rows.push(["Email", business.email ?? <Missing />]);
  rows.push(["Phone", business.phone ?? <Missing />]);
  rows.push(["Address", business.address ?? <Missing />]);
  rows.push([
    "Rating",
    business.rating === null
      ? <Missing />
      : business.review_count === null
        ? String(business.rating)
        : `${business.rating} from ${business.review_count} reviews`,
  ]);
  rows.push(["Found via", business.source ? sourceLabel(business.source) : <Missing />]);
  if (business.google_maps_url) {
    rows.push([
      "Map",
      <a key="map" href={business.google_maps_url} target="_blank" rel="noreferrer" className={linkClasses}>
        Open in Maps
      </a>,
    ]);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contact details</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col divide-y divide-rule/70 text-sm">
          {rows.map(([label, value]) => (
            <div key={label} className="grid grid-cols-[84px_minmax(0,1fr)] gap-3 py-2 first:pt-0 last:pb-0">
              <dt className="text-graphite">{label}</dt>
              <dd className="break-words text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}

const SOURCE_LABELS: Record<string, string> = {
  openstreetmap: "OpenStreetMap",
  geoapify: "Geoapify",
  csv: "CSV import",
  manual: "Added by hand",
  prepared_demo: "Sample data",
};

function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source.charAt(0).toUpperCase() + source.slice(1).replace(/_/g, " ");
}

function Missing() {
  return <span className="text-graphite">Not found</span>;
}

// Opportunity scores use the green meter; website quality is a grade of the
// site itself (higher is a better site), so it shows as a number and its badge.
function ScoreSummary({ audit }: { audit: WebsiteAudit }) {
  const opportunities: [string, number | null][] = [
    ["Overall", audit.overall_opportunity_score],
    ["Redesign", audit.redesign_opportunity_score],
    ["AI and automation", audit.ai_opportunity_score],
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Opportunity scores</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col gap-2.5 text-sm">
          {opportunities.map(([label, score]) => (
            <div key={label} className="flex items-center justify-between gap-3">
              <dt className="text-graphite">{label}</dt>
              <dd>
                <SignalMeter score={score} showWord={false} />
              </dd>
            </div>
          ))}
          <div className="mt-1 flex items-center justify-between gap-3 border-t border-rule/70 pt-3">
            <dt className="text-graphite">Website quality</dt>
            <dd className="flex items-center gap-2">
              <span className="tabular-nums text-ink">{audit.website_quality_score ?? "–"}</span>
              <QualityBadge category={audit.quality_category} />
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
