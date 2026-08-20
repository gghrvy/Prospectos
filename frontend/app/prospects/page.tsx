"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { OpportunityScoreBadge, QualityBadge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { api, ApiError } from "@/lib/api";
import { WEBSITE_STATUSES, type BusinessListItem } from "@/lib/types";

const LIMIT = 25;

export default function ProspectsPage() {
  const [items, setItems] = useState<BusinessListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [category, setCategory] = useState("");
  const [websiteStatus, setWebsiteStatus] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [auditing, setAuditing] = useState(false);
  const [auditProgress, setAuditProgress] = useState<{ done: number; total: number } | null>(null);
  const [auditResult, setAuditResult] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .listBusinesses({
        search: search || undefined,
        city: city || undefined,
        category: category || undefined,
        website_status: websiteStatus || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load prospects."))
      .finally(() => setLoading(false));
  }, [search, city, category, websiteStatus, sortBy, sortDir, offset]);

  useEffect(() => {
    load();
  }, [load]);

  // Selection is page-scoped (matches what's actually visible/checkable) --
  // clear it whenever the underlying rows change so a stale checked id from
  // a previous page/filter can't get silently deleted.
  useEffect(() => {
    setSelected(new Set());
  }, [items]);

  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    load();
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

  async function handleDeleteOne(id: string, name: string) {
    if (!confirm(`Delete "${name}" and all of its audit/outreach/note history? This cannot be undone.`)) return;
    try {
      await api.deleteBusiness(id);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  async function handleAuditSelected() {
    if (selected.size === 0) return;
    const ids = [...selected];
    setAuditing(true);
    setAuditResult(null);
    setError(null);
    // Sequential, not Promise.all: each audit launches a real headless
    // browser to crawl the site -- running many at once risks overloading
    // this machine and makes any single failure harder to attribute.
    let succeeded = 0;
    let failed = 0;
    for (let i = 0; i < ids.length; i++) {
      setAuditProgress({ done: i, total: ids.length });
      try {
        await api.runAudit(ids[i]);
        succeeded++;
      } catch {
        failed++;
      }
    }
    setAuditProgress(null);
    setAuditing(false);
    setAuditResult(
      `Audited ${succeeded} of ${ids.length}${failed > 0 ? ` (${failed} failed — often a site blocking automated visits, not a bug)` : ""}.`
    );
    setSelected(new Set());
    load();
  }

  async function handleDeleteSelected() {
    if (selected.size === 0) return;
    if (
      !confirm(
        `Delete ${selected.size} selected prospect(s) and all of their audit/outreach/note history? This cannot be undone.`
      )
    )
      return;
    setDeleting(true);
    setError(null);
    try {
      await Promise.all([...selected].map((id) => api.deleteBusiness(id)));
      setSelected(new Set());
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    try {
      const result = await api.importCSV(file);
      setImportResult(
        `Imported ${result.imported} of ${result.total_rows} rows (${result.skipped_duplicates} duplicates skipped).`
      );
      setOffset(0);
      load();
    } catch (err) {
      setImportResult(err instanceof ApiError ? `Import failed: ${err.message}` : "Import failed.");
    } finally {
      setImporting(false);
      e.target.value = "";
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Prospects</h1>
          <p className="font-mono text-xs text-muted-foreground">{total} total</p>
        </div>
        <div className="flex gap-2">
          {selected.size > 0 && (
            <>
              <Button variant="outline" disabled={auditing || deleting} onClick={handleAuditSelected}>
                {auditing
                  ? `Auditing ${auditProgress ? auditProgress.done + 1 : 1}/${auditProgress?.total ?? selected.size}…`
                  : `Run audit on selected (${selected.size})`}
              </Button>
              <Button variant="outline" disabled={deleting || auditing} onClick={handleDeleteSelected}>
                {deleting ? "Deleting…" : `Delete selected (${selected.size})`}
              </Button>
            </>
          )}
          <Button variant="outline" onClick={() => setShowAddForm((v) => !v)}>
            {showAddForm ? "Cancel" : "Add manually"}
          </Button>
          <Button variant="outline" disabled={importing} onClick={() => fileInputRef.current?.click()}>
            {importing ? "Importing…" : "Import CSV"}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
          <a href={api.exportCSVUrl()}>
            <Button variant="outline">Export CSV</Button>
          </a>
        </div>
      </div>

      {importResult && <p className="text-sm text-muted-foreground">{importResult}</p>}
      {auditResult && <p className="text-sm text-muted-foreground">{auditResult}</p>}

      {showAddForm && <AddProspectForm onCreated={() => { setShowAddForm(false); load(); }} />}

      <form onSubmit={applyFilters} className="flex flex-wrap items-end gap-3 rounded-lg border border-border p-4">
        <div>
          <Label>Search name</Label>
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. Plumbing" />
        </div>
        <div>
          <Label>City</Label>
          <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Houston" />
        </div>
        <div>
          <Label>Category</Label>
          <Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Plumber" />
        </div>
        <div>
          <Label>Website status</Label>
          <Select value={websiteStatus} onChange={(e) => setWebsiteStatus(e.target.value)}>
            <option value="">Any</option>
            {WEBSITE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Sort by</Label>
          <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="created_at">Date added</option>
            <option value="name">Name</option>
            <option value="city">City</option>
            <option value="category">Category</option>
            <option value="rating">Rating</option>
            <option value="review_count">Review count</option>
          </Select>
        </div>
        <div>
          <Label>Direction</Label>
          <Select value={sortDir} onChange={(e) => setSortDir(e.target.value as "asc" | "desc")}>
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </Select>
        </div>
        <Button type="submit">Apply</Button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-panel-raised text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              <th className="w-8 px-4 py-2 font-medium">
                <input
                  type="checkbox"
                  checked={items.length > 0 && selected.size === items.length}
                  onChange={toggleAll}
                  aria-label="Select all"
                />
              </th>
              <th className="px-4 py-2 font-medium">Business</th>
              <th className="px-4 py-2 font-medium">Category</th>
              <th className="px-4 py-2 font-medium">City</th>
              <th className="px-4 py-2 font-medium">Website</th>
              <th className="px-4 py-2 font-medium">Quality</th>
              <th className="px-4 py-2 font-medium">Opportunity</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-muted-foreground">
                  No prospects match these filters.
                </td>
              </tr>
            ) : (
              items.map((b) => (
                <tr key={b.id} className="border-t border-border hover:bg-white/5">
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(b.id)}
                      onChange={() => toggleOne(b.id)}
                      aria-label={`Select ${b.name}`}
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Link href={`/prospects/${b.id}`} className="font-medium hover:underline">
                      {b.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{b.category ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{b.city ?? "—"}</td>
                  <td className="px-4 py-2">
                    {b.website ? (
                      <a
                        href={b.website}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        visit
                      </a>
                    ) : b.social_url ? (
                      <a
                        href={b.social_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {b.social_url.includes("instagram.com") ? "Instagram" : "Facebook"}
                      </a>
                    ) : (
                      <span className="text-muted-foreground">no website</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <QualityBadge category={b.latest_quality_category} />
                  </td>
                  <td className="px-4 py-2">
                    <OpportunityScoreBadge score={b.latest_opportunity_score} />
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge status={b.current_status} />
                  </td>
                  <td className="px-4 py-2">
                    <button
                      type="button"
                      onClick={() => handleDeleteOne(b.id, b.name)}
                      className="font-mono text-[10px] uppercase tracking-wider text-red-400 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Showing {items.length === 0 ? 0 : offset + 1}–{offset + items.length} of {total}
        </span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + LIMIT >= total}
            onClick={() => setOffset(offset + LIMIT)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}

function AddProspectForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [city, setCity] = useState("");
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.createBusiness({
        name,
        category: category || null,
        city: city || null,
        website: website || null,
        phone: phone || null,
        email: email || null,
        source: "manual",
      });
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create prospect.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3 rounded-lg border border-border p-4">
      <div>
        <Label>Name *</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div>
        <Label>Category</Label>
        <Input value={category} onChange={(e) => setCategory(e.target.value)} />
      </div>
      <div>
        <Label>City</Label>
        <Input value={city} onChange={(e) => setCity(e.target.value)} />
      </div>
      <div>
        <Label>Website</Label>
        <Input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…" />
      </div>
      <div>
        <Label>Phone</Label>
        <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
      </div>
      <div>
        <Label>Email</Label>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <Button type="submit" disabled={saving}>
        {saving ? "Saving…" : "Add prospect"}
      </Button>
      {error && <span className="text-sm text-red-400">{error}</span>}
    </form>
  );
}
