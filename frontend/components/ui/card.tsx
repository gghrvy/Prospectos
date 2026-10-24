import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("relative rounded-lg border border-border/80 bg-panel", className)}
      {...props}
    />
  );
}

// A primary panel gets a hairline signal-colored top edge — reserved for
// the one or two panels per page that matter most (e.g. the audit summary),
// so it reads as emphasis rather than decoration.
export function PrimaryCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
  <Card className={cn("border-t-2 border-t-signal/70 shadow-[0_12px_36px_rgba(0,0,0,.16)]", className)} {...props} />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1 p-4 pb-2", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-sm font-semibold tracking-tight text-foreground", className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4 pt-2", className)} {...props} />;
}
