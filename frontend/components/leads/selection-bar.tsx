"use client";

import { AnimatePresence, motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { DURATION, exit } from "@/lib/motion";

// Floats over the list while leads are selected; bulk actions live here only.
export function SelectionBar({
  count,
  auditProgress,
  busy,
  onAudit,
  onDelete,
  onClear,
}: {
  count: number;
  auditProgress: { done: number; total: number } | null;
  busy: boolean;
  onAudit: () => void;
  onDelete: () => void;
  onClear: () => void;
}) {
  const shown = count > 0 || auditProgress !== null;
  return (
    <AnimatePresence>
      {shown && (
        <motion.div
          key="selection-bar"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0, transition: { duration: DURATION.base } }}
          exit={{ opacity: 0, transition: { duration: exit(DURATION.base) } }}
          role="region"
          aria-label="Selected leads"
          className="fixed inset-x-4 bottom-4 z-30 mx-auto flex max-w-lg flex-wrap items-center justify-between gap-3 rounded-panel border border-rule bg-sheet px-4 py-2.5 shadow-float"
        >
          <span className="text-sm font-medium tabular-nums text-ink" aria-live="polite">
            {auditProgress ? `Auditing ${auditProgress.done + 1} of ${auditProgress.total}` : `${count} selected`}
          </span>
          <div className="flex gap-1.5">
            <Button size="sm" variant="outline" disabled={busy} onClick={onAudit}>
              Run audit
            </Button>
            <Button size="sm" variant="outline" disabled={busy} onClick={onDelete} className="text-brick hover:text-brick">
              Delete
            </Button>
            <Button size="sm" variant="ghost" disabled={busy} onClick={onClear}>
              Clear
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
