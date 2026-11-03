import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

// Shared by Input, Select and Textarea so every field looks and focuses alike.
export const fieldClasses =
  "w-full rounded-control border border-rule bg-sheet text-sm text-ink placeholder:text-graphite/70 transition-colors duration-fast ease-assay hover:border-graphite/40 focus:border-survey focus:outline-none focus-visible:ring-2 focus-visible:ring-survey/20 disabled:cursor-not-allowed disabled:opacity-45";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return <input ref={ref} className={cn(fieldClasses, "h-9 px-3", className)} {...props} />;
  }
);
Input.displayName = "Input";
