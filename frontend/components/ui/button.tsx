import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

type Variant = "default" | "outline" | "ghost" | "destructive";
type Size = "sm" | "md";

const variantClasses: Record<Variant, string> = {
  default: "bg-survey text-sheet hover:bg-survey/90 active:bg-survey/80",
  outline: "border border-rule bg-sheet text-ink hover:border-graphite/40 hover:bg-paper active:bg-rule/40",
  ghost: "bg-transparent text-ink hover:bg-ink/[0.05] active:bg-ink/[0.08]",
  destructive: "bg-brick text-sheet hover:bg-brick/90 active:bg-brick/80",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px]",
  md: "h-9 px-4 text-sm",
};

const baseClasses =
  "focus-ring inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-control font-medium transition-colors duration-fast ease-assay disabled:cursor-not-allowed disabled:opacity-45";

// For links that should look like buttons, so an <a> never wraps a <button>.
export function buttonClasses(variant: Variant = "default", size: Size = "md", className?: string) {
  return cn(baseClasses, variantClasses[variant], sizeClasses[size], className);
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", type = "button", ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        className={buttonClasses(variant, size, className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
