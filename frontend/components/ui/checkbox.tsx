import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

// A native checkbox (keeps keyboard, form and screen-reader behavior) drawn in
// the Assay palette. The check mark is a CSS mask so it inherits `sheet`.
export const Checkbox = forwardRef<HTMLInputElement, Omit<InputHTMLAttributes<HTMLInputElement>, "type">>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        type="checkbox"
        className={cn(
          "assay-checkbox focus-ring relative h-4 w-4 shrink-0 cursor-pointer appearance-none rounded-[3px] border border-graphite/50 bg-sheet transition-colors duration-fast ease-assay",
          "hover:border-survey checked:border-survey checked:bg-survey disabled:cursor-not-allowed disabled:opacity-45",
          className
        )}
        {...props}
      />
    );
  }
);
Checkbox.displayName = "Checkbox";
