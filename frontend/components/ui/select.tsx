import { type SelectHTMLAttributes, forwardRef } from "react";

import { fieldClasses } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => {
    return <select ref={ref} className={cn(fieldClasses, "h-9 w-auto cursor-pointer pl-3 pr-8", className)} {...props} />;
  }
);
Select.displayName = "Select";
