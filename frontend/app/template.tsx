import type { ReactNode } from "react";

// Re-mounts on every route change, so each page arrives with a short fade
// and 4px rise. A CSS animation rather than framer-motion: it plays while the
// next page is still fetching and hydrating, and CSS runs off the main thread.
// No exit animation on routes.
export default function Template({ children }: { children: ReactNode }) {
  return <div className="animate-assay-enter">{children}</div>;
}
