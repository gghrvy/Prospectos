"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp } from "lucide-react";

import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Menu, type MenuItem } from "@/components/ui/menu";
import type { BusinessListItem } from "@/lib/types";
import { cn, hostOf } from "@/lib/utils";

export type SortDir = "asc" | "desc";

const dateFormat = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" });

function Website({ business }: { business: BusinessListItem }) {
  const link = "focus-ring rounded-tag text-survey hover:underline";
  if (business.website) {
    return (
      <a href={business.website} target="_blank" rel="noreferrer" className={cn(link, "block max-w-[11rem] truncate")} title={business.website}>
        {hostOf(business.website)}
      </a>
    );
  }
  if (business.social_url) {
    return (
      <a href={business.social_url} target="_blank" rel="noreferrer" className={link}>
        Social only
      </a>
    );
  }
  return <span className="text-graphite">No website</span>;
}

function SortHeader({
  label,
  field,
  sortBy,
  sortDir,
  onSort,
  className,
}: {
  label: string;
  field: string;
  sortBy: string;
  sortDir: SortDir;
  onSort: (field: string) => void;
  className?: string;
}) {
  const active = sortBy === field;
  const Arrow = sortDir === "asc" ? ArrowUp : ArrowDown;
  return (
    <th scope="col" className={className} aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
      <button
        type="button"
        onClick={() => onSort(field)}
        className={cn(
          "focus-ring -mx-1 inline-flex items-center gap-1 rounded-tag px-1 transition-colors duration-fast ease-assay hover:text-ink",
          active && "text-ink"
        )}
      >
        {label}
        <Arrow size={12} aria-hidden="true" className={active ? "opacity-100" : "opacity-0"} />
      </button>
    </th>
  );
}

function LeadName({ business }: { business: BusinessListItem }) {
  return (
    <Link href={`/prospects/${business.id}`} className="focus-ring block truncate rounded-tag font-serif text-[15px] font-medium text-ink hover:underline">
      {business.name}
    </Link>
  );
}

export function LeadsTable({
  items,
  selected,
  onToggle,
  onToggleAll,
  sortBy,
  sortDir,
  onSort,
  onDelete,
  active,
  demo,
}: {
  items: BusinessListItem[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
  sortBy: string;
  sortDir: SortDir;
  onSort: (field: string) => void;
  onDelete: (business: BusinessListItem) => void;
  active: number;
  demo: boolean;
}) {
  const router = useRouter();
  const allSelected = items.length > 0 && selected.size === items.length;

  function rowMenu(business: BusinessListItem) {
    const menuItems: MenuItem[] = [{ label: "Open", onSelect: () => router.push(`/prospects/${business.id}`) }];
    if (!demo) menuItems.push({ label: "Delete lead", onSelect: () => onDelete(business), tone: "danger" });
    return <Menu label={`Actions for ${business.name}`} items={menuItems} />;
  }

  return (
    <>
      {/* Wide screens: the full table. */}
      <div className="data-table hidden md:block">
        <table className="text-sm">
          <thead>
            <tr>
              {!demo && (
                <th scope="col" className="w-10 pr-0">
                  <Checkbox
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = selected.size > 0 && !allSelected;
                    }}
                    onChange={onToggleAll}
                    aria-label="Select all leads on this page"
                  />
                </th>
              )}
              <SortHeader label="Lead" field="name" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <th scope="col">Website</th>
              <th scope="col">Quality</th>
              <th scope="col">Opportunity</th>
              <th scope="col">Stage</th>
              <SortHeader label="Added" field="created_at" sortBy={sortBy} sortDir={sortDir} onSort={onSort} className="hidden xl:table-cell" />
              <th scope="col" className="w-12">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((b, i) => (
              <tr
                key={b.id}
                aria-selected={i === active}
                data-row-index={i}
                className={cn(i === active && "bg-survey/[0.06] shadow-[inset_2px_0_0_rgb(var(--survey))]")}
              >
                {!demo && (
                  <td className="pr-0">
                    <Checkbox checked={selected.has(b.id)} onChange={() => onToggle(b.id)} aria-label={`Select ${b.name}`} />
                  </td>
                )}
                <td className="max-w-[18rem] py-2">
                  <LeadName business={b} />
                  {b.category && <span className="block truncate text-xs text-graphite">{b.category}</span>}
                  {b.city && <span className="block truncate text-xs text-graphite">{b.city}</span>}
                </td>
                <td>
                  <Website business={b} />
                </td>
                <td>
                  <QualityBadge category={b.latest_quality_category} />
                </td>
                <td className="whitespace-nowrap">
                  <OpportunityScoreBadge score={b.latest_opportunity_score} />
                </td>
                <td>
                  <StatusBadge status={b.current_status} />
                </td>
                <td className="hidden whitespace-nowrap text-[13px] tabular-nums text-graphite xl:table-cell">
                  {dateFormat.format(new Date(b.created_at))}
                </td>
                <td className="text-right">{rowMenu(b)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Narrow screens: a two-line list instead of a sideways-scrolling table. */}
      <ul className="overflow-hidden rounded-panel border border-rule bg-sheet md:hidden">
        {items.map((b, i) => (
          <li
            key={b.id}
            aria-selected={i === active}
            className={cn("flex items-start gap-3 border-t border-rule/70 px-4 py-3 first:border-t-0", i === active && "bg-survey/[0.06]")}
          >
            {!demo && (
              <Checkbox className="mt-1" checked={selected.has(b.id)} onChange={() => onToggle(b.id)} aria-label={`Select ${b.name}`} />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-3">
                <LeadName business={b} />
                <span className="shrink-0">
                  <OpportunityScoreBadge score={b.latest_opportunity_score} showWord={false} />
                </span>
              </div>
              <div className="mt-1 flex items-center justify-between gap-3">
                <span className="truncate text-xs text-graphite">{[b.category, b.city].filter(Boolean).join(", ")}</span>
                <StatusBadge status={b.current_status} />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
