import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// A load that failed: what didn't load, why, and a way to try again.
export function ErrorState({
  title,
  body,
  onRetry,
  className,
}: {
  title: string;
  body: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div role="alert" className={cn("rounded-panel border border-brick/30 bg-brick/[0.05] p-4", className)}>
      <p className="text-sm font-medium text-brick">{title}</p>
      <p className="mt-1 max-w-prose text-sm leading-6 text-ink">{body}</p>
      {onRetry && (
        <Button size="sm" variant="outline" className="mt-3" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
