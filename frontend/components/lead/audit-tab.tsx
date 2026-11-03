"use client";

import { Button } from "@/components/ui/button";
import { SignalMeter } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { activityTime } from "@/lib/activity";
import { api } from "@/lib/api";
import { OPPORTUNITY_TYPE_LABELS, type WebsiteAudit } from "@/lib/types";
import { cn } from "@/lib/utils";

export function AuditTab({
  audits,
  onRunAudit,
  auditing,
  demo,
}: {
  audits: WebsiteAudit[];
  onRunAudit: () => void;
  auditing: boolean;
  demo: boolean;
}) {
  const sorted = [...audits].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const audit = sorted[0];

  if (!audit) {
    return (
      <EmptyState
        title="No audit yet"
        body="The audit checks mobile layout, design, technical health, content and how easy it is to get in touch, then lists the evidence behind each score."
        action={
          <Button variant="outline" onClick={onRunAudit} disabled={auditing}>
            {auditing ? "Auditing…" : "Run audit"}
          </Button>
        }
      />
    );
  }

  const subScores: [string, number | null][] = [
    ["Mobile", audit.mobile_score],
    ["Design", audit.design_score],
    ["Technical", audit.technical_score],
    ["Content", audit.content_score],
    ["Conversion", audit.conversion_score],
    ["Customer experience", audit.customer_experience_score],
  ];

  const facts = [
    audit.url && `${audit.page_count ?? 0} ${audit.page_count === 1 ? "page" : "pages"} read, ${audit.crawl_depth ?? 0} ${audit.crawl_depth === 1 ? "level" : "levels"} deep`,
    audit.https_enabled !== null && (audit.https_enabled ? "Served over HTTPS" : "Not served over HTTPS"),
    audit.broken_link_count !== null &&
      (audit.broken_link_count === 0 ? "No broken links" : `${audit.broken_link_count} broken ${audit.broken_link_count === 1 ? "link" : "links"}`),
  ].filter(Boolean) as string[];

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-w-0 flex-col gap-6">
        <Card>
          <CardHeader className="flex-row flex-wrap items-baseline justify-between gap-x-4">
            <CardTitle>Latest audit</CardTitle>
            <span className="text-[13px] text-graphite">
              {demo ? "Prepared sample audit, " : ""}
              {activityTime(audit.created_at)}
            </span>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            {audit.audit_summary && <p className="max-w-prose text-sm leading-6 text-ink">{audit.audit_summary}</p>}

            {audit.opportunity_reasons && audit.opportunity_reasons.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-ink">Why it scored this way</h3>
                <ul className="mt-2 flex max-w-prose flex-col gap-2">
                  {audit.opportunity_reasons.map((reason, i) => (
                    <li key={i} className="flex gap-3 text-sm leading-6 text-ink">
                      <span className="mt-[11px] h-1 w-1 shrink-0 rounded-full bg-graphite" aria-hidden="true" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {(audit.opportunity_types ?? []).length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-ink">Opportunity areas</h3>
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {(audit.opportunity_types ?? []).map((type) => (
                    <li key={type} className="rounded-tag border border-survey/25 bg-survey/[0.06] px-2 py-0.5 text-[13px] text-survey">
                      {OPPORTUNITY_TYPE_LABELS[type] ?? type}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {facts.length > 0 && (
              <ul className="flex flex-wrap gap-x-5 gap-y-1 border-t border-rule/70 pt-4 text-[13px] text-graphite">
                {facts.map((fact) => (
                  <li key={fact}>{fact}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {(audit.screenshot_desktop_path || audit.screenshot_mobile_path) && (
          <Card>
            <CardHeader>
              <CardTitle>Screenshots</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-start gap-4">
              {audit.screenshot_desktop_path && <Screenshot label="Desktop" path={audit.screenshot_desktop_path} />}
              {audit.screenshot_mobile_path && <Screenshot label="Mobile" path={audit.screenshot_mobile_path} />}
            </CardContent>
          </Card>
        )}
      </div>

      <aside className="flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Website scores</CardTitle>
            <p className="text-[13px] leading-5 text-graphite">How well the current site does. Lower scores leave more room to help.</p>
          </CardHeader>
          <CardContent>
            <dl className="flex flex-col gap-3">
              {subScores.map(([label, score]) => (
                <SubScore key={label} label={label} score={score} />
              ))}
            </dl>
          </CardContent>
        </Card>

        {sorted.length > 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Earlier audits</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col divide-y divide-rule/70 text-sm">
                {sorted.slice(1).map((past) => (
                  <li key={past.id} className="flex items-center justify-between gap-3 py-2 first:pt-0 last:pb-0">
                    <span className="text-graphite">{activityTime(past.created_at)}</span>
                    <SignalMeter score={past.overall_opportunity_score} showWord={false} />
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </aside>
    </div>
  );
}

// Site-quality bars: ink when the site does well, ochre and brick as it falls
// short. The number always sits beside the bar so color never carries it alone.
function SubScore({ label, score }: { label: string; score: number | null }) {
  const tone = score === null ? "" : score >= 70 ? "bg-ink/70" : score >= 40 ? "bg-ochre" : "bg-brick";
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_32px] items-center gap-x-3 gap-y-1">
      <dt className="text-[13px] text-graphite">{label}</dt>
      <dd className="contents">
        <span className="row-span-2 text-right text-sm font-medium tabular-nums text-ink">{score ?? "–"}</span>
        <span className="block h-1.5 overflow-hidden rounded-full bg-rule" aria-hidden="true">
          {score !== null && (
            <span
              className={cn("block h-full origin-left rounded-full", tone)}
              style={{ transform: `scaleX(${Math.max(0, Math.min(100, score)) / 100})` }}
            />
          )}
        </span>
      </dd>
    </div>
  );
}

function Screenshot({ label, path }: { label: string; path: string }) {
  const url = api.screenshotUrl(path);
  if (!url) return null;
  return (
    <figure className="flex flex-col gap-1.5">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={url} alt={`${label} screenshot of the website`} loading="lazy" className="max-h-72 rounded-control border border-rule" />
      <figcaption className="text-xs text-graphite">{label}</figcaption>
    </figure>
  );
}
