import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "h-10 rounded-md border border-border bg-panel-raised/40 px-3 text-sm focus:border-signal/70 focus:outline-none focus:ring-2 focus:ring-signal/15",
          className
        )}
        {...props}
      />
    );
  }
);
Select.displayName = "Select";
