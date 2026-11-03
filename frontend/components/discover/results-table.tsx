"use client";

import { type ReactNode, useEffect, useState } from "react";

import { AnimatePresence, motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Select } from "@/components/ui/select";
import { DURATION, exit } from "@/lib/motion";
import type { DiscoveredBusiness } from "@/lib/types";
import { cn, hostOf } from "@/lib/utils";

const CHAIN = /\b(inc\.?|llc|ltd\.?|corp\.?|co\.?|franchise|[0-9]+ locations?)\b/i;

type Presence = "any" | "has" | "none";

export function ResultsTable({
  results,
  saving,
  auditing,
  onSave,
  onSaveAndAudit,
}: {
  results: DiscoveredBusiness[];
  saving: boolean;
  auditing: { done: number; total: number } | null;
  onSave: (chosen: DiscoveredBusiness[]) => void;
  onSaveAndAudit: (chosen: DiscoveredBusiness[]) => void;
}) {
  // Keyed by index into `results`; cleared when a new search replaces them.
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [minimumFit, setMinimumFit] = useState(0);
  const [minimumReviews, setMinimumReviews] = useState(0);
  const [website, setWebsite] = useState<Presence>("any");
  const [contact, setContact] = useState<Presence>("any");
  const [emailOnly, setEmailOnly] = useState(false);
  const [excludeChains, setExcludeChains] = useState(true);

  useEffect(() => {
    setSelected(new Set());
  }, [results]);

  const visibleIndexes = results.flatMap((item, index) => {
    const hasContact = Boolean(item.email || item.phone || item.website || item.social_url);
    const keep =
      (item.prospect_fit_score ?? 0) >= minimumFit &&
      (item.review_count ?? 0) >= minimumReviews &&
      (website === "any" || (website === "has" ? Boolean(item.website) : !item.website)) &&
      (contact === "any" || (contact === "has" ? hasContact : !hasContact)) &&
      (!emailOnly || Boolean(item.email)) &&
      (!excludeChains || !CHAIN.test(item.name));
    return keep ? [index] : [];
  });
  const selectedVisible = visibleIndexes.filter((index) => selected.has(index)).length;
  const allSelected = visibleIndexes.length > 0 && selectedVisible === visibleIndexes.length;
  const busy = saving || auditing !== null;
  const chosen = () => results.filter((_, index) => selected.has(index));

  function toggle(index: number) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  function toggleAll() {
    setSelected((current) => {
      const next = new Set(current);
      for (const index of visibleIndexes) {
        if (allSelected) next.delete(index);
        else next.add(index);
      }
      return next;
    });
  }

  return (
    <section aria-labelledby="results-heading" className={cn("flex flex-col gap-3", (selected.size > 0 || auditing) && "pb-16")}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="results-heading" className="text-base font-semibold text-ink">
            {results.length === 0 ? "No businesses found" : `${results.length} ${results.length === 1 ? "business" : "businesses"} found`}
          </h2>
          {results.length > 0 && visibleIndexes.length !== results.length && (
            <p className="text-[13px] text-graphite">{visibleIndexes.length} match your filters</p>
          )}
        </div>
        {results.length > 0 && (
          <Button size="sm" variant="outline" disabled={busy} onClick={() => onSave(results)}>
            {saving ? "Saving…" : `Save all ${results.length} as leads`}
          </Button>
        )}
      </div>

      {results.length === 0 ? (
        <Card className="px-4 py-5 text-sm leading-6 text-graphite">
          Nothing came back for that search. Try a wider radius, a broader category such as &quot;restaurant&quot;, or check the
          spelling of the place.
        </Card>
      ) : (
        <>
          <fieldset className="flex flex-wrap items-end gap-x-4 gap-y-3 rounded-panel border border-rule bg-sheet px-4 py-3">
            <legend className="sr-only">Filter results</legend>
            <Filter id="filter-fit" label="Fit">
              <Select id="filter-fit" value={minimumFit} onChange={(e) => setMinimumFit(Number(e.target.value))}>
                <option value={0}>Any</option>
                <option value={50}>50 or more</option>
                <option value={70}>70 or more</option>
              </Select>
            </Filter>
            <Filter id="filter-reviews" label="Reviews">
              <Select id="filter-reviews" value={minimumReviews} onChange={(e) => setMinimumReviews(Number(e.target.value))}>
                <option value={0}>Any</option>
                <option value={10}>10 or more</option>
                <option value={50}>50 or more</option>
                <option value={100}>100 or more</option>
              </Select>
            </Filter>
            <Filter id="filter-website" label="Website">
              <Select id="filter-website" value={website} onChange={(e) => setWebsite(e.target.value as Presence)}>
                <option value="any">Any</option>
                <option value="has">Has a website</option>
                <option value="none">No website</option>
              </Select>
            </Filter>
            <Filter id="filter-contact" label="Contact">
              <Select id="filter-contact" value={contact} onChange={(e) => setContact(e.target.value as Presence)}>
                <option value="any">Any</option>
                <option value="has">Some way to reach them</option>
                <option value="none">No contact details</option>
              </Select>
            </Filter>
            <label className="flex h-9 items-center gap-2 text-[13px] text-ink">
              <Checkbox checked={emailOnly} onChange={(e) => setEmailOnly(e.target.checked)} />
              Has an email
            </label>
            <label className="flex h-9 items-center gap-2 text-[13px] text-ink">
              <Checkbox checked={excludeChains} onChange={(e) => setExcludeChains(e.target.checked)} />
              Hide likely chains
            </label>
          </fieldset>

          {visibleIndexes.length === 0 ? (
            <Card className="px-4 py-5 text-sm text-graphite">No results match these filters. Loosen one to see more.</Card>
          ) : (
            <div className="data-table">
              <table className="text-sm">
                <thead>
                  <tr>
                    <th className="w-10 !pr-0">
                      <Checkbox
                        aria-label="Select every result shown"
                        checked={allSelected}
                        ref={(el) => {
                          if (el) el.indeterminate = selectedVisible > 0 && !allSelected;
                        }}
                        onChange={toggleAll}
                      />
                    </th>
                    <th className="w-[38%]">Business</th>
                    <th>Fit</th>
                    <th className="hidden md:table-cell">Phone</th>
                    <th className="hidden sm:table-cell">Website</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleIndexes.map((index) => {
                    const r = results[index];
                    return (
                      <tr key={index} className={selected.has(index) ? "bg-survey/[0.05]" : undefined}>
                        <td className="!pr-0">
                          <Checkbox aria-label={`Select ${r.name}`} checked={selected.has(index)} onChange={() => toggle(index)} />
                        </td>
                        <td className="py-2 sm:min-w-[180px]">
                          <span className="block font-medium text-ink">{r.name}</span>
                          <span className="block text-xs text-graphite">{r.address ?? r.category ?? "No address listed"}</span>
                        </td>
                        <td className="py-2">
                          {r.prospect_fit_score == null ? (
                            <span className="text-graphite">Not rated</span>
                          ) : (
                            <span className="font-medium tabular-nums text-ink">{r.prospect_fit_score}</span>
                          )}
                          {r.prospect_fit_reason && <span className="hidden max-w-[220px] truncate text-xs text-graphite sm:block">{r.prospect_fit_reason}</span>}
                        </td>
                        <td className="hidden whitespace-nowrap text-graphite md:table-cell">{r.phone ?? "None listed"}</td>
                        <td className="hidden sm:table-cell">
                          {r.website ? (
                            <a href={r.website} target="_blank" rel="noreferrer" className="focus-ring rounded-[2px] text-survey hover:underline">
                              {hostOf(r.website)}
                            </a>
                          ) : r.social_url ? (
                            <a href={r.social_url} target="_blank" rel="noreferrer" className="focus-ring rounded-[2px] text-survey hover:underline">
                              {r.social_url.includes("instagram.com") ? "Instagram" : "Facebook"}
                            </a>
                          ) : (
                            <span className="text-graphite">None found</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <AnimatePresence>
        {(selected.size > 0 || auditing) && (
          <motion.div
            key="selection-bar"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0, transition: { duration: DURATION.base } }}
            exit={{ opacity: 0, transition: { duration: exit(DURATION.base) } }}
            role="region"
            aria-label="Selected results"
            className="fixed inset-x-4 bottom-4 z-30 mx-auto flex max-w-lg flex-wrap items-center justify-between gap-3 rounded-panel border border-rule bg-sheet px-4 py-2.5 shadow-float"
          >
            <span className="text-sm font-medium tabular-nums text-ink" aria-live="polite">
              {auditing ? `Auditing ${auditing.done + 1} of ${auditing.total}` : `${selected.size} selected`}
            </span>
            <div className="flex gap-1.5">
              <Button size="sm" variant="outline" disabled={busy} onClick={() => onSave(chosen())}>
                Save as leads
              </Button>
              <Button size="sm" disabled={busy} onClick={() => onSaveAndAudit(chosen())}>
                Save and audit
              </Button>
              <Button size="sm" variant="ghost" disabled={busy} onClick={() => setSelected(new Set())}>
                Clear
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function Filter({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col">
      <label htmlFor={id} className="mb-1 text-xs font-medium text-graphite">
        {label}
      </label>
      {children}
    </div>
  );
}
