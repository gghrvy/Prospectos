import type { Metadata } from "next";
import type { ReactNode } from "react";

// Working screens, not landing pages: titled, but kept out of search in every build.
export const metadata: Metadata = {
  title: "Outreach",
  robots: { index: false, follow: true },
  alternates: { canonical: null },
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
