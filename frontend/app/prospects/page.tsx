"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, Search } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { LeadsTable, type SortDir } from "@/components/leads/leads-table";
import { SelectionBar } from "@/components/leads/selection-bar";
import { useShortcut } from "@/components/shell/shortcuts";
import { DemoNotice, PageHeader } from "@/components/shell/page-header";
import { Button, buttonClasses } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Menu } from "@/components/ui/menu";
import { Select } from "@/components/ui/select";
import { LoadingRegion, SkeletonRows } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";
import { WEBSITE_STATUSES, type BusinessListItem } from "@/lib/types";

const LIMIT = 25;
const FILTER_DELAY_MS = 300;

const SORTS: { field: string; label: string; dir: SortDir }[] = [
  { field: "created_at", label: "Date added", dir: "desc" },
  { field: "name", label: "Name", dir: "asc" },
  { field: "city", label: "City", dir: "asc" },
  { field: "category", label: "Category", dir: "asc" },
  { field: "rating", label: "Rating", dir: "desc" },
  { field: "review_count", label: "Review count", dir: "desc" },
];

const WEBSITE_LABELS: Record<string, string> = { exists: "Has a website", not_found: "No website found", unreachable: "Unreachable" };

function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function message(err: unknown, fallback: string) {
  return err instanceof ApiError ? err.message : fallback;
}

export default function ProspectsPage() {
  const router = useRouter();
  const confirm = useConfirm();

  const [items, setItems] = useState<BusinessListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [filters, setFilters] = useState({ search: "", city: "", category: "", websiteStatus: "" });
  const applied = useDebounced(filters, FILTER_DELAY_MS);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [active, setActive] = useState(-1);
  const [busy, setBusy] = useState(false);
  const [auditProgress, setAuditProgress] = useState<{ done: number; total: number } | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .listBusinesses({
        search: applied.search || undefined,
        city: applied.city || undefined,
        category: applied.category || undefined,
        website_status: applied.websiteStatus || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => setError(message(err, "The API didn't answer. Check that it's running, then try again.")))
      .finally(() => setLoading(false));
  }, [applied, sortBy, sortDir, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // A filter or sort change starts again from the first page.
  useEffect(() => {
    setOffset(0);
  }, [applied, sortBy, sortDir]);

  // Selection is page-scoped: clear it whenever the rows change, so an id from
  // a previous page or filter can never be deleted out of sight.
  useEffect(() => {
    setSelected(new Set());
    setActive(-1);
  }, [items]);

  function updateFilter(key: keyof typeof filters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function sortOn(field: string) {
    if (field === sortBy) {
      setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDir(SORTS.find((s) => s.field === field)?.dir ?? "asc");
    }
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => (prev.size === items.length ? new Set() : new Set(items.map((b) => b.id))));
  }

  // Keyboard: / search, j/k move, Enter open, x select.
  useEffect(() => {
    if (active < 0) return;
    const rows = [...document.querySelectorAll<HTMLElement>('[aria-selected="true"]')];
    rows.find((row) => row.offsetParent !== null)?.scrollIntoView({ block: "nearest" });
  }, [active]);
  useShortcut("/", () => searchRef.current?.focus());
  useShortcut("j", () => setActive((i) => Math.min(i + 1, items.length - 1)));
  useShortcut("k", () => setActive((i) => Math.max(i - 1, 0)));
  useShortcut("Enter", () => {
    if (items[active]) router.push(`/prospects/${items[active].id}`);
  });
  useShortcut("x", () => {
    if (items[active]) toggleOne(items[active].id);
  }, !isDemoMode);

  async function deleteOne(business: BusinessListItem) {
    const ok = await confirm({
      title: "Delete this lead?",
      body: `${business.name} and all of its audits, drafts and notes will be removed. This can't be undone.`,
      confirmLabel: "Delete lead",
      tone: "danger",
    });
    if (!ok) return;
    try {
      await api.deleteBusiness(business.id);
      toast(`Deleted ${business.name}.`);
      load();
    } catch (err) {
      toast(message(err, "The lead couldn't be deleted."), "error");
    }
  }

  async function deleteSelected() {
    const count = selected.size;
    const ok = await confirm({
      title: `Delete ${count} ${count === 1 ? "lead" : "leads"}?`,
      body: "Their audits, drafts and notes will be removed too. This can't be undone.",
      confirmLabel: count === 1 ? "Delete lead" : `Delete ${count} leads`,
      tone: "danger",
    });
    if (!ok) return;
    setBusy(true);
    try {
      await Promise.all([...selected].map((id) => api.deleteBusiness(id)));
      toast(`Deleted ${count} ${count === 1 ? "lead" : "leads"}.`);
      load();
    } catch (err) {
      toast(message(err, "Some leads couldn't be deleted."), "error");
    } finally {
      setBusy(false);
    }
  }

  async function auditSelected() {
    const ids = [...selected];
    setBusy(true);
    // Sequential, not Promise.all: each audit launches a real headless
    // browser to crawl the site -- running many at once risks overloading
    // this machine and makes any single failure harder to attribute.
    let succeeded = 0;
    for (let i = 0; i < ids.length; i++) {
      setAuditProgress({ done: i, total: ids.length });
      try {
        await api.runAudit(ids[i]);
        succeeded++;
      } catch {
        // counted below
      }
    }
    const failed = ids.length - succeeded;
    setAuditProgress(null);
    setBusy(false);
    toast(
      `Audited ${succeeded} of ${ids.length}.` +
        (failed > 0 ? ` ${failed} failed, usually because the site blocks automated visits.` : ""),
      failed > 0 ? "error" : "success"
    );
    load();
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const result = await api.importCSV(file);
      toast(`Imported ${result.imported} of ${result.total_rows} rows. ${result.skipped_duplicates} duplicates skipped.`);
      setOffset(0);
      load();
    } catch (err) {
      toast(`Import failed: ${message(err, "the file couldn't be read.")}`, "error");
    } finally {
      setImporting(false);
      e.target.value = "";
    }
  }

  const page = Math.floor(offset / LIMIT) + 1;
  const pages = Math.max(1, Math.ceil(total / LIMIT));
  const currentSort = SORTS.find((s) => s.field === sortBy);
  const filtered = Object.values(applied).some(Boolean);

  return (
    <div className="flex flex-col gap-6">
      <DemoNotice>These fictional leads are prepared examples. Open one to replay its sample audit; adding, importing and deleting are turned off.</DemoNotice>

      <PageHeader
        title="Leads"
        meta={loading && total === 0 ? undefined : `${total} ${total === 1 ? "lead" : "leads"}${filtered ? " match these filters" : ""}`}
        actions={
          !isDemoMode && (
            <>
              <Button variant="outline" onClick={() => setShowAddForm((v) => !v)} aria-expanded={showAddForm}>
                {showAddForm ? "Cancel" : "Add lead"}
              </Button>
              <Button variant="outline" disabled={importing} onClick={() => fileInputRef.current?.click()}>
                {importing ? "Importing" : "Import CSV"}
              </Button>
              <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleImport} tabIndex={-1} />
              <a href={api.exportCSVUrl()} className={buttonClasses("ghost")}>
                Export CSV
              </a>
            </>
          )
        }
      />

      {showAddForm && (
        <AddLeadForm
          onCreated={(name) => {
            setShowAddForm(false);
            toast(`Added ${name}.`);
            load();
          }}
        />
      )}

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[240px] flex-[2]">
          <Label htmlFor="lead-search">Search</Label>
          <div className="relative">
            <Search size={15} aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-graphite" />
            <Input
              id="lead-search"
              ref={searchRef}
              type="search"
              value={filters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
              onKeyDown={(e) => e.key === "Escape" && e.currentTarget.blur()}
              placeholder="Business, city or category"
              className="pl-9 pr-9"
            />
            <kbd className="pointer-events-none absolute right-2.5 top-1/2 hidden -translate-y-1/2 rounded-tag sm:block border border-rule px-1.5 text-[11px] text-graphite">/</kbd>
          </div>
        </div>
        <div className="min-w-[140px] flex-1">
          <Label htmlFor="lead-city">City</Label>
          <Input id="lead-city" value={filters.city} onChange={(e) => updateFilter("city", e.target.value)} placeholder="Any city" />
        </div>
        <div className="min-w-[140px] flex-1">
          <Label htmlFor="lead-category">Category</Label>
          <Input id="lead-category" value={filters.category} onChange={(e) => updateFilter("category", e.target.value)} placeholder="Any category" />
        </div>
        <div className="min-w-[150px] flex-1">
          <Label htmlFor="lead-website">Website</Label>
          <Select id="lead-website" value={filters.websiteStatus} onChange={(e) => updateFilter("websiteStatus", e.target.value)}>
            <option value="">Any</option>
            {WEBSITE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {WEBSITE_LABELS[s] ?? s}
              </option>
            ))}
          </Select>
        </div>
        <Menu
          label="Sort leads"
          className="h-9 border border-rule bg-sheet text-ink"
          trigger={
            <>
              <span className="text-graphite">Sort</span> {currentSort?.label ?? sortBy}
              <ChevronDown size={14} aria-hidden="true" />
            </>
          }
          items={SORTS.map((s) => ({
            label: s.label,
            checked: s.field === sortBy,
            onSelect: () => {
              setSortBy(s.field);
              setSortDir(s.dir);
            },
          }))}
        />
      </div>

      {error ? (
        <ErrorState title="Your leads didn't load" body={error} onRetry={load} />
      ) : loading && items.length === 0 ? (
        <LoadingRegion label="Loading leads">
          <SkeletonRows rows={8} />
        </LoadingRegion>
      ) : items.length === 0 ? (
        filtered ? (
          <EmptyState
            title="No leads match these filters"
            body="Try a shorter search or clear a filter."
            action={
              <Button size="sm" variant="outline" onClick={() => setFilters({ search: "", city: "", category: "", websiteStatus: "" })}>
                Clear filters
              </Button>
            }
          />
        ) : (
          <EmptyState
            title="No leads yet"
            body={isDemoMode ? "The sample leads aren't available right now." : "Search for local businesses, import a CSV, or add one by hand."}
            action={
              !isDemoMode && (
                <Link href="/discover" className={buttonClasses("outline", "sm")}>
                  Find leads
                </Link>
              )
            }
          />
        )
      ) : (
        <div className={loading ? "opacity-60 transition-opacity duration-base ease-assay" : "transition-opacity duration-base ease-assay"} aria-busy={loading}>
          <LeadsTable
            items={items}
            selected={selected}
            onToggle={toggleOne}
            onToggleAll={toggleAll}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={sortOn}
            onDelete={deleteOne}
            active={active}
            demo={isDemoMode}
          />
        </div>
      )}

      {total > LIMIT && (
        <nav aria-label="Pages" className="flex items-center justify-between gap-4 text-[13px] text-graphite">
          <span className="tabular-nums">
            Page {page} of {pages}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={offset + LIMIT >= total} onClick={() => setOffset(offset + LIMIT)}>
              Next
            </Button>
          </div>
        </nav>
      )}

      {!isDemoMode && (
        <SelectionBar
          count={selected.size}
          auditProgress={auditProgress}
          busy={busy}
          onAudit={auditSelected}
          onDelete={deleteSelected}
          onClear={() => setSelected(new Set())}
        />
      )}
    </div>
  );
}

function AddLeadForm({ onCreated }: { onCreated: (name: string) => void }) {
  const [values, setValues] = useState({ name: "", category: "", city: "", website: "", phone: "", email: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fields: { key: keyof typeof values; label: string; type?: string; placeholder?: string }[] = [
    { key: "name", label: "Business name" },
    { key: "category", label: "Category" },
    { key: "city", label: "City" },
    { key: "website", label: "Website", type: "url", placeholder: "https://" },
    { key: "phone", label: "Phone", type: "tel" },
    { key: "email", label: "Email", type: "email" },
  ];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!values.name.trim()) {
      setError("Add the business name to save this lead.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.createBusiness({
        name: values.name,
        category: values.category || null,
        city: values.city || null,
        website: values.website || null,
        phone: values.phone || null,
        email: values.email || null,
        source: "manual",
      });
      onCreated(values.name);
    } catch (err) {
      setError(message(err, "The lead couldn't be saved."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="flex flex-col gap-4 p-4">
        <h2 className="text-base font-semibold text-ink">Add a lead by hand</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {fields.map((field) => (
            <div key={field.key}>
              <Label htmlFor={`add-${field.key}`}>
                {field.label}
                {field.key === "name" && <span className="text-brick"> *</span>}
              </Label>
              <Input
                id={`add-${field.key}`}
                type={field.type ?? "text"}
                value={values[field.key]}
                placeholder={field.placeholder}
                required={field.key === "name"}
                autoFocus={field.key === "name"}
                onChange={(e) => setValues((prev) => ({ ...prev, [field.key]: e.target.value }))}
              />
            </div>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving" : "Save lead"}
          </Button>
          {error && (
            <span role="alert" className="text-sm text-brick">
              {error}
            </span>
          )}
        </div>
      </form>
    </Card>
  );
}
