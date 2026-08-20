"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, PrimaryCard } from "@/components/ui/card";
import { RadialGauge } from "@/components/ui/gauge";
import { api, ApiError } from "@/lib/api";
import type { BusinessListItem } from "@/lib/types";

export default function DashboardPage() {
  const [businesses, setBusinesses] = useState<BusinessListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listBusinesses({ limit: 200, sort_by: "created_at", sort_dir: "desc" })
      .then((res) => setBusinesses(res.items))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to reach the backend API."));
  }, []);

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

  return (
    <div className="flex flex-col gap-6">
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

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[auto_1fr]">
        <PrimaryCard className="flex flex-col items-center justify-center gap-2 px-10 py-6">
          <RadialGauge score={stats?.avgScore ?? null} label="Avg. opportunity across audited prospects" />
        </PrimaryCard>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard label="Total prospects" value={stats?.total} />
          <StatCard label="No website found" value={stats?.noWebsite} />
          <StatCard label="High opportunity (70+)" value={stats?.highOpportunity} highlight />
          <StatCard label="Audited" value={stats?.audited} />
          <StatCard label="Won" value={stats?.won} />
        </div>
      </div>

      <Card>
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

function StatCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: number | undefined;
  highlight?: boolean;
}) {
  return (
    <Card className="bracket-hover">
      <CardHeader className="pb-0">
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent className="pt-1">
        <span className={`font-mono text-4xl font-semibold tabular-nums tracking-tight ${highlight ? "text-signal" : ""}`}>
          {value === undefined ? "—" : value}
        </span>
      </CardContent>
    </Card>
  );
}
