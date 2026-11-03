import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingRegion, Skeleton } from "@/components/ui/skeleton";
import { activityLabel, activityTime, activityTone } from "@/lib/activity";
import type { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export type GmailActivity = Awaited<ReturnType<typeof api.gmailActivity>>;

const TONE_CLASS = { good: "text-ink", bad: "text-brick", pending: "text-graphite" } as const;

// Gmail actions, newest first, under today's send count. Shared by the
// dashboard and the Outreach page.
export function ActivityFeed({
  activity,
  limit = 8,
  unavailable = false,
}: {
  activity: GmailActivity | null;
  limit?: number;
  unavailable?: boolean;
}) {
  if (unavailable) {
    return (
      <Card>
        <EmptyState bare title="Email activity isn't available" body="The API didn't answer for Gmail activity. It shows up here once the backend is reachable." />
      </Card>
    );
  }
  if (activity === null) {
    return (
      <LoadingRegion label="Loading activity">
        <Card>
          <div className="border-b border-rule px-4 py-3">
            <Skeleton className="h-3.5 w-3/5" />
          </div>
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex justify-between gap-4 border-t border-rule/70 px-4 py-3 first:border-t-0">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3.5 w-1/3" />
                <Skeleton className="h-3 w-2/3" />
              </div>
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </Card>
      </LoadingRegion>
    );
  }
  return (
    <Card>
      <p className="border-b border-rule px-4 py-3 text-[13px] text-graphite">
        <span className="font-medium tabular-nums text-ink">
          {activity.sent_today} of {activity.daily_limit}
        </span>{" "}
        emails sent today. Batches share this daily limit.
      </p>
      {activity.items.length === 0 ? (
        <EmptyState bare title="No email activity yet" body="Approvals, batches, sends and replies are listed here as they happen." />
      ) : (
        <ul>
          {activity.items.slice(0, limit).map((item) => (
            <li key={item.id} className="flex items-start justify-between gap-4 border-t border-rule/70 px-4 py-2.5 text-[13px] first:border-t-0">
              <span className="min-w-0">
                <span className={cn("font-medium", TONE_CLASS[activityTone(item.action)])}>{activityLabel(item.action)}</span>
                {item.detail && <span className="block truncate text-graphite">{item.detail}</span>}
              </span>
              <time dateTime={item.created_at} className="shrink-0 text-xs tabular-nums text-graphite">
                {activityTime(item.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
