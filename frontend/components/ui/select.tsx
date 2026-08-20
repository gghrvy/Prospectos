import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "h-9 rounded-sm border border-border bg-panel px-2 text-sm focus:outline-none focus:ring-1 focus:ring-signal",
          className
        )}
        {...props}
      />
    );
  }
);
Select.displayName = "Select";
