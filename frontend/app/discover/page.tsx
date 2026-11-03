"use client";

import Link from "next/link";
import { type ReactNode, useEffect, useState } from "react";

import { ResultsTable } from "@/components/discover/results-table";
import { useSaveResults } from "@/components/discover/use-save-results";
import { MapPicker } from "@/components/map-picker";
import { DemoNotice, PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";
import type { DiscoveredBusiness } from "@/lib/types";
import { cn } from "@/lib/utils";

type Mode = "city" | "map";

const DEFAULT_CENTER = { lat: 40.7128, lng: -74.006 }; // New York City
const QUICK_PICKS = ["plumber", "electrician", "dentist", "lawyer", "salon", "retail"];
const SEARCH_NOTE = "Searching OpenStreetMap. A wide area or a broad category can take up to a minute.";

// The demo runs the same search, capped to match the backend's demo limits
// (demo_limits.py), and its results can't be saved or audited.
const LIMITS = isDemoMode ? { radiusKm: 10, results: 25 } : { radiusKm: 50, results: 200 };
const DEFAULT_LIMIT = isDemoMode ? 25 : 50;

export default function DiscoverPage() {
  const [mode, setMode] = useState<Mode>("city");
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    // Non-fatal: the category field still takes free text without suggestions.
    api
      .searchCategories()
      .then((res) => setCategories(res.categories))
      .catch(() => {});
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <DemoNotice>
        Search here is live: results are real public listings from OpenStreetMap, shown up to {LIMITS.results} at a time. In the
        demo they aren&apos;t saved or audited.
      </DemoNotice>
      <PageHeader
        title="Discover"
        description="Search OpenStreetMap for local businesses. No Google Maps scraping and no paid APIs."
        meta={
          isDemoMode ? undefined : (
            <>
              Have a list already?{" "}
              <Link href="/prospects" className="focus-ring rounded-[2px] text-survey underline-offset-2 hover:underline">
                Import a CSV from Leads
              </Link>
            </>
          )
        }
      />

      <div role="group" aria-label="Search by" className="inline-flex self-start rounded-control border border-rule bg-sheet p-0.5">
        <ModeOption active={mode === "city"} onSelect={() => setMode("city")}>
          City
        </ModeOption>
        <ModeOption active={mode === "map"} onSelect={() => setMode("map")}>
          Map area
        </ModeOption>
      </div>

      {mode === "city" ? <CitySearch categories={categories} /> : <MapSearch categories={categories} />}
    </div>
  );
}

function ModeOption({ active, onSelect, children }: { active: boolean; onSelect: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onSelect}
      className={cn(
        "focus-ring h-8 rounded-[5px] px-3.5 text-[13px] font-medium transition-colors duration-fast ease-assay",
        active ? "bg-ink text-sheet" : "text-graphite hover:bg-ink/[0.05] hover:text-ink"
      )}
    >
      {children}
    </button>
  );
}

function CategoryField({
  id,
  value,
  onChange,
  categories,
  optional = false,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  categories: string[];
  optional?: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div>
        <Label htmlFor={id}>
          Business category{" "}
          {optional ? (
            <span className="font-normal">(optional)</span>
          ) : (
            <span className="text-brick" aria-hidden="true">
              *
            </span>
          )}
        </Label>
        <Input
          id={id}
          list={`${id}-known`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={!optional}
          aria-describedby={`${id}-help`}
          placeholder={optional ? "Every business in the area" : "Pharmacy"}
        />
        <datalist id={`${id}-known`}>
          {categories.map((category) => (
            <option key={category} value={category} />
          ))}
        </datalist>
        <p id={`${id}-help`} className="mt-1 text-xs leading-5 text-graphite">
          {optional
            ? "Leave blank to include every type. Separate terms with commas to search several, such as cafe, bakery."
            : categories.length > 0
              ? `${categories.length} known categories match a precise map tag. Other words work too, with fewer results.`
              : "Type any business category."}
        </p>
      </div>
      <div role="group" aria-label="Quick picks" className="flex flex-wrap gap-1.5">
        {QUICK_PICKS.map((pick) => {
          const active = value.trim().toLowerCase() === pick;
          return (
            <button
              key={pick}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(pick)}
              className={cn(
                "focus-ring h-7 rounded-tag border px-2.5 text-[13px] transition-colors duration-fast ease-assay",
                active ? "border-ink bg-ink text-sheet" : "border-rule bg-sheet text-ink hover:border-graphite/40 hover:bg-paper"
              )}
            >
              {pick.charAt(0).toUpperCase() + pick.slice(1)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SearchFeedback({ searching, error }: { searching: boolean; error: string | null }) {
  return (
    <>
      {searching && (
        <p role="status" className="text-[13px] text-graphite">
          {SEARCH_NOTE}
        </p>
      )}
      {error && <ErrorState title="The search didn't finish" body={error} />}
    </>
  );
}

function CitySearch({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [radiusKm, setRadiusKm] = useState(5);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [cityCheck, setCityCheck] = useState<{ status: "idle" | "checking" | "valid" | "invalid"; label?: string }>({ status: "idle" });
  const [results, setResults] = useState<DiscoveredBusiness[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saver = useSaveResults();

  // Checks the typed place against the geocoder, so a typo shows up before
  // the slow search runs.
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

  async function search(event: React.FormEvent) {
    event.preventDefault();
    if (!category.trim() || !city.trim()) {
      setError("Add a category and a city to search.");
      return;
    }
    setSearching(true);
    setError(null);
    try {
      const found = await api.searchOSM({ category, city, country: country || undefined, radius_km: radiusKm, limit, save: false });
      setResults(found as DiscoveredBusiness[]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The search didn't finish. Check that the API is running, then try again.");
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card className="p-5">
        <form onSubmit={search} className="flex flex-col gap-5">
          <div className="max-w-xl">
            <CategoryField id="city-category" value={category} onChange={setCategory} categories={categories} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_110px_110px_auto] lg:items-start">
            <div>
              <Label htmlFor="city">
                City{" "}
                <span className="text-brick" aria-hidden="true">
                  *
                </span>
              </Label>
              <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} required placeholder="Houston" aria-describedby="city-check" />
              <p id="city-check" aria-live="polite" className="mt-1 min-h-5 truncate text-xs leading-5" title={cityCheck.label}>
                {cityCheck.status === "checking" && <span className="text-graphite">Checking the place…</span>}
                {cityCheck.status === "valid" && <span className="text-ink">Found {cityCheck.label}</span>}
                {cityCheck.status === "invalid" && <span className="text-brick">No place by that name. Check the spelling.</span>}
              </p>
            </div>
            <div>
              <Label htmlFor="country">Country</Label>
              <Input id="country" value={country} onChange={(e) => setCountry(e.target.value)} placeholder="USA" />
            </div>
            <div>
              <Label htmlFor="radius">Radius, km</Label>
              <Input id="radius" type="number" min={1} max={LIMITS.radiusKm} value={radiusKm} onChange={(e) => setRadiusKm(Number(e.target.value))} />
            </div>
            <div>
              <Label htmlFor="limit">Max results</Label>
              <Input id="limit" type="number" min={1} max={LIMITS.results} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
            </div>
            <Button type="submit" disabled={searching} className="sm:col-span-2 lg:col-span-1 lg:mt-[22px]">
              {searching ? "Searching…" : "Search"}
            </Button>
          </div>
        </form>
      </Card>

      <SearchFeedback searching={searching} error={error} />

      {results && (
        <DiscoverResults results={results} saver={saver} />
      )}
    </div>
  );
}

function MapSearch({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [center, setCenter] = useState(DEFAULT_CENTER);
  const [radiusKm, setRadiusKm] = useState(5);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [place, setPlace] = useState("");
  const [locating, setLocating] = useState(false);
  const [results, setResults] = useState<DiscoveredBusiness[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saver = useSaveResults();

  async function locate(event: React.FormEvent) {
    event.preventDefault();
    if (!place.trim()) return;
    setLocating(true);
    setError(null);
    try {
      const result = await api.geocode(place);
      setCenter({ lat: result.latitude, lng: result.longitude });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That place couldn't be found. Check the spelling.");
    } finally {
      setLocating(false);
    }
  }

  async function search() {
    setSearching(true);
    setError(null);
    try {
      const found = await api.searchOSM({ category, latitude: center.lat, longitude: center.lng, radius_km: radiusKm, limit, save: false });
      setResults(found as DiscoveredBusiness[]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The search didn't finish. Check that the API is running, then try again.");
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card className="grid overflow-hidden lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="flex flex-col gap-5 border-b border-rule p-5 lg:border-b-0 lg:border-r">
          <form onSubmit={locate}>
            <Label htmlFor="map-place">Go to a place</Label>
            <div className="flex gap-2">
              <Input id="map-place" value={place} onChange={(e) => setPlace(e.target.value)} placeholder="Miami, FL" />
              <Button type="submit" variant="outline" disabled={locating}>
                {locating ? "Finding…" : "Go"}
              </Button>
            </div>
          </form>
          <CategoryField id="map-category" value={category} onChange={setCategory} categories={categories} optional />
          <div>
            <Label htmlFor="map-radius">
              Radius <span className="font-normal tabular-nums text-ink">{radiusKm} km</span>
            </Label>
            <input
              id="map-radius"
              type="range"
              min={1}
              max={LIMITS.radiusKm}
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="focus-ring w-full cursor-pointer accent-survey"
            />
          </div>
          <div className="max-w-[120px]">
            <Label htmlFor="map-limit">Max results</Label>
            <Input id="map-limit" type="number" min={1} max={LIMITS.results} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          </div>
          <Button onClick={() => void search()} disabled={searching}>
            {searching ? "Searching…" : "Search this area"}
          </Button>
        </div>
        <div className="flex min-h-[340px] flex-col lg:min-h-[460px]">
          <div className="relative flex-1 bg-paper">
            <div className="absolute inset-0">
              <MapPicker latitude={center.lat} longitude={center.lng} radiusKm={radiusKm} onCenterChange={(lat, lng) => setCenter({ lat, lng })} />
            </div>
          </div>
          <p className="border-t border-rule px-4 py-2 text-xs text-graphite">Click the map or drag the pin to move the center of the search.</p>
        </div>
      </Card>

      <SearchFeedback searching={searching} error={error} />

      {results && (
        <DiscoverResults results={results} saver={saver} />
      )}
    </div>
  );
}

function DiscoverResults({ results, saver }: { results: DiscoveredBusiness[]; saver: ReturnType<typeof useSaveResults> }) {
  if (isDemoMode) return <ResultsTable results={results} />;
  return (
    <ResultsTable
      results={results}
      saving={saver.saving}
      auditing={saver.auditProgress}
      onSave={(chosen) => void saver.save(chosen)}
      onSaveAndAudit={(chosen) => void saver.saveAndAudit(chosen)}
    />
  );
}
