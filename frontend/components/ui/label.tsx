import type { LabelHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1 block font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground", className)}
      {...props}
    />
  );
}
