// Wording and tone for Gmail activity rows, shared by the dashboard and Outreach.
const LABELS: Record<string, string> = {
  SENT: "Email sent",
  SEND_FAILED: "Send failed",
  REPLIED: "Reply received",
  APPROVED: "Draft approved",
  QUEUED: "Queued for sending",
};

export function activityLabel(action: string): string {
  return LABELS[action] ?? action.charAt(0) + action.slice(1).toLowerCase().replace(/_/g, " ");
}

export type ActivityTone = "good" | "bad" | "pending";

export function activityTone(action: string): ActivityTone {
  if (action === "SEND_FAILED") return "bad";
  if (action === "SENT" || action === "REPLIED" || action === "APPROVED") return "good";
  return "pending";
}

const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function activityTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : dateFormat.format(date);
}
