"use client";

import { useState } from "react";

import { useToast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api";
import type { DiscoveredBusiness } from "@/lib/types";

// Save (and optionally audit, one at a time) the chosen search results.
// Shared by the city and map searches so both report the same way.
export function useSaveResults() {
  const [saving, setSaving] = useState(false);
  const [auditProgress, setAuditProgress] = useState<{ done: number; total: number } | null>(null);
  const toast = useToast();

  async function save(chosen: DiscoveredBusiness[]) {
    if (!chosen.length) return;
    setSaving(true);
    try {
      const saved = await api.saveBusinesses(chosen);
      const skipped = chosen.length - saved.length;
      toast(`Saved ${saved.length} ${saved.length === 1 ? "lead" : "leads"}${skipped ? `. ${skipped} already in your leads were skipped` : ""}.`);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "The leads couldn't be saved. Try again.", "error");
    } finally {
      setSaving(false);
    }
  }

  async function saveAndAudit(chosen: DiscoveredBusiness[]) {
    if (!chosen.length) return;
    setSaving(true);
    try {
      const saved = await api.saveBusinesses(chosen);
      setSaving(false);
      let failed = 0;
      for (let index = 0; index < saved.length; index += 1) {
        setAuditProgress({ done: index, total: saved.length });
        try {
          await api.runAudit(saved[index].id);
        } catch {
          failed += 1;
        }
      }
      const skipped = chosen.length - saved.length;
      toast(
        `Saved and audited ${saved.length - failed} of ${saved.length}` +
        (failed ? `. ${failed} audits failed and can be re-run from the lead` : "") +
        (skipped ? `. ${skipped} already in your leads were skipped and not re-audited` : "") +
        ".",
        failed ? "error" : "success"
      );
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "The leads couldn't be saved. Try again.", "error");
    } finally {
      setSaving(false);
      setAuditProgress(null);
    }
  }

  return { saving, auditProgress, save, saveAndAudit };
}
