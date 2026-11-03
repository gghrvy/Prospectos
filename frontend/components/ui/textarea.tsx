import { type TextareaHTMLAttributes, forwardRef } from "react";

import { fieldClasses } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return <textarea ref={ref} className={cn(fieldClasses, "px-3 py-2 leading-6", className)} {...props} />;
  }
);
Textarea.displayName = "Textarea";
