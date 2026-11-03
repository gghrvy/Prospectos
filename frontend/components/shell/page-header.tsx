import type { ReactNode } from "react";

import { isDemoMode } from "@/lib/runtime";

export function PageHeader({
  title,
  description,
  actions,
  meta,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
      <div className="min-w-0 max-w-2xl">
        <h1 className="font-serif text-[28px] font-medium leading-[34px] tracking-[-0.01em] text-ink">{title}</h1>
        {description && <p className="mt-1.5 text-sm leading-6 text-graphite">{description}</p>}
        {meta && <div className="mt-2 text-[13px] text-graphite">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

// The one demo-mode notice, so every page says it the same way.
export function DemoNotice({ children }: { children: ReactNode }) {
  if (!isDemoMode) return null;
  return (
    <aside className="flex gap-3 rounded-panel border border-survey/25 bg-survey/[0.06] px-4 py-3 text-[13px] leading-5 text-ink">
      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-survey" aria-hidden="true" />
      <p>
        <span className="font-medium">Public demo.</span> {children}
      </p>
    </aside>
  );
}
