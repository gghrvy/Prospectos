import { cn } from "@/lib/utils";

// A placeholder block shaped like the content that is loading. Drawn in the
// rule tone (a sheet block would vanish on a sheet card); the pulse stops
// under reduced motion via the global rule in globals.css.
export function Skeleton({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cn("block animate-assay-pulse rounded-tag bg-rule/60", className)} />;
}

// The announcement that goes with a group of skeletons, so screen readers
// hear one "Loading leads" instead of nothing.
export function LoadingRegion({ label, className, children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div role="status" aria-label={label} aria-busy="true" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}

// Rows of a list or table: a title line and a shorter detail line.
export function SkeletonRows({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("divide-y divide-rule/70 rounded-panel border border-rule bg-sheet", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3">
          <div className="flex-1 space-y-2">
            <Skeleton className={cn("h-3.5", i % 3 === 0 ? "w-2/5" : i % 3 === 1 ? "w-1/3" : "w-1/2")} />
            <Skeleton className="h-3 w-1/4" />
          </div>
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}
