// This controls presentation only. A production build defaults to the safe
// public demo unless explicitly configured for live mode; `npm run dev`
// remains live by default. The backend setting is the security boundary.
const configuredDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE;
export const isDemoMode = configuredDemoMode === "true" || (
  configuredDemoMode === undefined && process.env.NODE_ENV === "production"
);
