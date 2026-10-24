import { type TextareaHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "w-full rounded-md border border-border bg-panel-raised/40 px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-signal/70 focus:outline-none focus:ring-2 focus:ring-signal/15",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";
