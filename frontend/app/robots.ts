import type { MetadataRoute } from "next";

import { isDemoMode } from "@/lib/runtime";

// The public demo may be crawled (inner pages carry noindex themselves, so
// crawlers must be allowed to read it); a live build is internal and closed.
export default function robots(): MetadataRoute.Robots {
  return isDemoMode ? { rules: { userAgent: "*", allow: "/" } } : { rules: { userAgent: "*", disallow: "/" } };
}
