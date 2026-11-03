import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

// A panel is a filled sheet laid on the paper: no shadow, one hairline edge.
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("relative rounded-panel border border-rule bg-sheet", className)} {...props} />;
}

// The one or two panels per page that carry the page's main finding get a
// survey-green top rule, so emphasis comes from a single line, not decoration.
export function PrimaryCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <Card className={cn("border-t-2 border-t-survey", className)} {...props} />;
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1 p-4 pb-2", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-base font-semibold text-ink", className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4 pt-2", className)} {...props} />;
}
