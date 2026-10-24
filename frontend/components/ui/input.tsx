import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-md border border-border bg-panel-raised/40 px-3 text-sm placeholder:text-muted-foreground focus:border-signal/70 focus:outline-none focus:ring-2 focus:ring-signal/15",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
