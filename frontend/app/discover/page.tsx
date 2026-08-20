"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MapPicker } from "@/components/map-picker";
import { api, ApiError } from "@/lib/api";
import type { DiscoveredBusiness } from "@/lib/types";

type Mode = "city" | "map";

const DEFAULT_CENTER = { lat: 40.7128, lng: -74.006 }; // New York City

export default function DiscoverPage() {
  const [mode, setMode] = useState<Mode>("city");
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    api
      .searchCategories()
      .then((res) => setCategories(res.categories))
      .catch(() => {
        // Non-fatal -- the category input still works as freeform text,
        // it just won't have autocomplete suggestions.
      });
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-wider text-signal">Discovery</p>
        <h1 className="text-3xl font-semibold tracking-tight">Discover prospects</h1>
        <p className="text-sm text-muted-foreground">
          Search OpenStreetMap for local businesses. No Google Maps scraping, no paid APIs.
          Prefer bulk import instead?{" "}
          <Link href="/prospects" className="text-signal hover:underline">
            Import a CSV from the Prospects page
          </Link>
          .
        </p>
      </div>

      <div className="flex gap-1 self-start rounded-sm border border-border p-1">
        <ModeButton active={mode === "city"} onClick={() => setMode("city")}>
          Search by city
        </ModeButton>
        <ModeButton active={mode === "map"} onClick={() => setMode("map")}>
          Search on map
        </ModeButton>
      </div>

      {mode === "city" ? <CitySearch categories={categories} /> : <MapSearch categories={categories} />}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-sm px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-colors ${
        active ? "bg-signal text-slate-950" : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function CategoryField({
  value,
  onChange,
  categories,
  optional = false,
}: {
  value: string;
  onChange: (v: string) => void;
  categories: string[];
  optional?: boolean;
}) {
  return (
    <div>
      <Label>Category {optional ? "(optional)" : "*"}</Label>
      <Input
        list="known-categories"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={optional ? "Leave blank for everything nearby" : "e.g. plumber"}
      />
      <datalist id="known-categories">
        {categories.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>
      <p className="mt-1 font-mono text-[10px] text-muted-foreground">
        {optional
          ? "Blank sweeps every business type in the radius. Comma-separate terms (e.g. \"cafe, restaurant\") to search several at once."
          : categories.length > 0
            ? `${categories.length} known categories map to a precise tag -- other terms still work but may return fewer results.`
            : "Loading known categories..."}
      </p>
    </div>
  );
}

function ResultsTable({
  results,
  saving,
  onSave,
}: {
  results: DiscoveredBusiness[] | null;
  saving: boolean;
  onSave: (chosen: DiscoveredBusiness[]) => void;
}) {
  // Keyed by array index into `results` — reset whenever a new search
  // replaces the results array, since the identity underneath each index
  // has changed.
  const [selected, setSelected] = useState<Set<number>>(new Set());

  useEffect(() => {
    setSelected(new Set());
  }, [results]);

  if (results === null) return null;

  const allSelected = results.length > 0 && selected.size === results.length;

  function toggleOne(i: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(results!.map((_, i) => i)));
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>{results.length} result(s)</CardTitle>
        {results.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] text-muted-foreground">{selected.size} selected</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onSave(results!)}
              disabled={saving}
            >
              {saving ? "Saving…" : "Save all as prospects"}
            </Button>
            <Button
              size="sm"
              onClick={() => onSave(results!.filter((_, i) => selected.has(i)))}
              disabled={saving || selected.size === 0}
            >
              {saving ? "Saving…" : `Save selected (${selected.size})`}
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0">
        {results.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">
            No results. Try a broader radius, a different category term, or check spelling of the city.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-t border-border text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <th className="w-8 px-4 py-2 font-medium">
                  <input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="Select all" />
                </th>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Address</th>
                <th className="px-4 py-2 font-medium">Phone</th>
                <th className="px-4 py-2 font-medium">Website</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-t border-border bracket-hover">
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(i)}
                      onChange={() => toggleOne(i)}
                      aria-label={`Select ${r.name}`}
                    />
                  </td>
                  <td className="px-4 py-2 font-medium">{r.name}</td>
                  <td className="px-4 py-2 text-muted-foreground">{r.address ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{r.phone ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {r.website ? (
                      <a href={r.website} target="_blank" rel="noreferrer" className="text-signal hover:underline">
                        visit
                      </a>
                    ) : r.social_url ? (
                      <a href={r.social_url} target="_blank" rel="noreferrer" className="text-signal hover:underline">
                        {r.social_url.includes("instagram.com") ? "Instagram" : "Facebook"}
                      </a>
                    ) : (
                      "no website"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

function CitySearch({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [radiusKm, setRadiusKm] = useState(5);
  const [limit, setLimit] = useState(50);

  const [cityCheck, setCityCheck] = useState<{ status: "idle" | "checking" | "valid" | "invalid"; label?: string }>({
    status: "idle",
  });

  const [results, setResults] = useState<DiscoveredBusiness[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Validates the typed city against the real geocoder (real API-backed
  // input, not a guess) so a typo surfaces before running the full search.
  useEffect(() => {
    if (!city.trim()) {
      setCityCheck({ status: "idle" });
      return;
    }
    setCityCheck({ status: "checking" });
    const handle = setTimeout(() => {
      api
        .geocode(country ? `${city}, ${country}` : city)
        .then((res) => setCityCheck({ status: "valid", label: res.display_name }))
        .catch(() => setCityCheck({ status: "invalid" }));
    }, 500);
    return () => clearTimeout(handle);
  }, [city, country]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!category.trim() || !city.trim()) {
      setError("Category and city are required.");
      return;
    }
    setSearching(true);
    setError(null);
    setSaveMessage(null);
    try {
      const found = await api.searchOSM({ category, city, country: country || undefined, radius_km: radiusKm, limit, save: false });
      setResults(found as DiscoveredBusiness[]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed. Is the backend reachable?");
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  async function handleSave(chosen: DiscoveredBusiness[]) {
    setSaving(true);
    setError(null);
    setSaveMessage(null);
    try {
      const saved = await api.saveBusinesses(chosen);
      setSaveMessage(
        `Saved ${saved.length} of ${chosen.length} selected (duplicates already in your DB were skipped).`
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>OpenStreetMap search</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-3">
            <CategoryField value={category} onChange={setCategory} categories={categories} />
            <div>
              <Label>City *</Label>
              <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Houston" />
              <p className="mt-1 font-mono text-[10px]">
                {cityCheck.status === "checking" && <span className="text-muted-foreground">checking…</span>}
                {cityCheck.status === "valid" && (
                  <span className="text-emerald-400" title={cityCheck.label}>
                    resolved: {cityCheck.label?.slice(0, 40)}
                    {(cityCheck.label?.length ?? 0) > 40 ? "…" : ""}
                  </span>
                )}
                {cityCheck.status === "invalid" && <span className="text-red-400">no match found</span>}
              </p>
            </div>
            <div>
              <Label>Country</Label>
              <Input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="e.g. USA" />
            </div>
            <div>
              <Label>Radius (km)</Label>
              <Input type="number" min={1} max={50} value={radiusKm} onChange={(e) => setRadiusKm(Number(e.target.value))} className="w-24" />
            </div>
            <div>
              <Label>Max results</Label>
              <Input type="number" min={1} max={200} value={limit} onChange={(e) => setLimit(Number(e.target.value))} className="w-24" />
            </div>
            <Button type="submit" disabled={searching}>
              {searching ? "Searching…" : "Search"}
            </Button>
          </form>
          {searching && (
            <p className="mt-2 font-mono text-[10px] text-muted-foreground">
              Querying free OpenStreetMap servers -- this can take up to a minute on a slow response, especially for
              a broad category or large radius.
            </p>
          )}
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {saveMessage && <p className="text-sm text-emerald-400">{saveMessage}</p>}

      <ResultsTable results={results} saving={saving} onSave={handleSave} />
    </div>
  );
}

function MapSearch({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [center, setCenter] = useState(DEFAULT_CENTER);
  const [radiusKm, setRadiusKm] = useState(5);
  const [limit, setLimit] = useState(50);
  const [recenterQuery, setRecenterQuery] = useState("");
  const [locating, setLocating] = useState(false);

  const [results, setResults] = useState<DiscoveredBusiness[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  async function handleLocate(e: React.FormEvent) {
    e.preventDefault();
    if (!recenterQuery.trim()) return;
    setLocating(true);
    setError(null);
    try {
      const result = await api.geocode(recenterQuery);
      setCenter({ lat: result.latitude, lng: result.longitude });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't find that place.");
    } finally {
      setLocating(false);
    }
  }

  async function handleSearch() {
    setSearching(true);
    setError(null);
    setSaveMessage(null);
    try {
      const found = await api.searchOSM({
        category,
        latitude: center.lat,
        longitude: center.lng,
        radius_km: radiusKm,
        limit,
        save: false,
      });
      setResults(found as DiscoveredBusiness[]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed. Is the backend reachable?");
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  async function handleSave(chosen: DiscoveredBusiness[]) {
    setSaving(true);
    setError(null);
    setSaveMessage(null);
    try {
      const saved = await api.saveBusinesses(chosen);
      setSaveMessage(
        `Saved ${saved.length} of ${chosen.length} selected (duplicates already in your DB were skipped).`
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="flex flex-col gap-4 pt-4">
          <div className="flex flex-wrap items-end gap-3">
            <CategoryField value={category} onChange={setCategory} categories={categories} optional />
            <form onSubmit={handleLocate} className="flex items-end gap-2">
              <div>
                <Label>Jump to a place</Label>
                <Input
                  value={recenterQuery}
                  onChange={(e) => setRecenterQuery(e.target.value)}
                  placeholder="e.g. Miami, FL"
                  className="w-56"
                />
              </div>
              <Button type="submit" variant="outline" disabled={locating}>
                {locating ? "Locating…" : "Locate"}
              </Button>
            </form>
            <div className="flex-1" />
            <Button onClick={handleSearch} disabled={searching}>
              {searching ? "Searching…" : "Search this area"}
            </Button>
          </div>
          {searching && (
            <p className="-mt-2 font-mono text-[10px] text-muted-foreground">
              Querying free OpenStreetMap servers -- this can take up to a minute on a slow response, especially for
              a broad category or large radius.
            </p>
          )}

          <div>
            <Label>
              Radius: <span className="text-foreground">{radiusKm} km</span>
            </Label>
            <input
              type="range"
              min={1}
              max={50}
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="w-full accent-signal"
            />
          </div>

          <div className="flex items-center gap-3">
            <Label className="mb-0">Max results</Label>
            <Input
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-24"
            />
            <p className="font-mono text-[10px] text-muted-foreground">
              Click the map (or drag the pin) to set the search center.
            </p>
          </div>

          <div className="bracket-frame h-[420px] overflow-hidden rounded-sm border border-border">
            <MapPicker
              latitude={center.lat}
              longitude={center.lng}
              radiusKm={radiusKm}
              onCenterChange={(lat, lng) => setCenter({ lat, lng })}
            />
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {saveMessage && <p className="text-sm text-emerald-400">{saveMessage}</p>}

      <ResultsTable results={results} saving={saving} onSave={handleSave} />
    </div>
  );
}
