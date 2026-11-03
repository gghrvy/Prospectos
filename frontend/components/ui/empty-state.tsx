import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

// What an empty list looks like everywhere: what's missing, how it fills up,
// and (when there is one) the next thing to do.
export function EmptyState({
  title,
  body,
  action,
  className,
  bare = false,
}: {
  title: string;
  body: ReactNode;
  action?: ReactNode;
  className?: string;
  // Inside a card that already draws the border.
  bare?: boolean;
}) {
  return (
    <div className={cn(bare ? "px-4 py-5" : "rounded-panel border border-rule bg-sheet p-5", className)}>
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-1 max-w-prose text-sm leading-6 text-graphite">{body}</p>
      {action && <div className="mt-3 flex flex-wrap gap-2">{action}</div>}
    </div>
  );
}
