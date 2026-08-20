import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("relative rounded-md border border-border bg-panel", className)}
      {...props}
    />
  );
}

// A primary panel gets a hairline signal-colored top edge — reserved for
// the one or two panels per page that matter most (e.g. the audit summary),
// so it reads as emphasis rather than decoration.
export function PrimaryCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <Card className={cn("bracket-frame border-t-2 border-t-signal/60", className)} {...props} />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1 p-4 pb-2", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground", className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4 pt-2", className)} {...props} />;
}
