import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";

import { MotionRoot } from "@/components/motion/motion-root";
import { MobileBar } from "@/components/shell/mobile-bar";
import { ShortcutsProvider } from "@/components/shell/shortcuts";
import { Sidebar } from "@/components/shell/sidebar";
import { ConfirmProvider } from "@/components/ui/confirm-dialog";
import { ToastProvider } from "@/components/ui/toast";
import { isDemoMode } from "@/lib/runtime";

import "./globals.css";

// Plex Serif and Plex Sans were drawn as one family, so the pairing reads as
// a single voice: serif for names, titles and grades (the "assay report"),
// sans with tabular figures for every working surface. See MASTER.md.
const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

const plexSerif = IBM_Plex_Serif({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-serif",
  display: "swap",
});

const DESCRIPTION =
  "A working demo of ProspectOS. It finds local businesses, audits their websites, scores each opportunity and drafts outreach that waits for human approval.";

// Only the public demo's landing page is meant for search. A live build is
// an internal tool and stays out of the index entirely; the demo's inner
// pages opt out in their own layouts. Canonical and Open Graph URLs need an
// absolute base: NEXT_PUBLIC_SITE_URL if set, else Vercel's production domain.
const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : undefined);

export const metadata: Metadata = {
  ...(SITE_URL ? { metadataBase: new URL(SITE_URL) } : {}),
  title: {
    default: "ProspectOS: local lead research and website audits",
    template: "%s | ProspectOS",
  },
  description: DESCRIPTION,
  alternates: { canonical: "/" },
  robots: isDemoMode ? { index: true, follow: true } : { index: false, follow: false },
  openGraph: {
    type: "website",
    siteName: "ProspectOS",
    title: "ProspectOS: local lead research and website audits",
    description: DESCRIPTION,
    url: "/",
  },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexSerif.variable}`}>
      <body>
        <a
          href="#main"
          className="focus-ring fixed left-4 top-3 z-50 -translate-y-20 rounded-control bg-survey px-3 py-2 text-sm font-medium text-sheet transition-transform duration-fast ease-assay focus-visible:translate-y-0"
        >
          Skip to content
        </a>
        <MotionRoot>
          <ShortcutsProvider>
            <ConfirmProvider>
              <ToastProvider>
                <div className="flex min-h-dvh">
                  <Sidebar />
                  <div className="flex min-w-0 flex-1 flex-col">
                    <MobileBar />
                    <main id="main" tabIndex={-1} className="mx-auto w-full max-w-[1200px] px-4 py-6 outline-none sm:px-6 sm:py-8 lg:px-8">
                      {children}
                    </main>
                  </div>
                </div>
              </ToastProvider>
            </ConfirmProvider>
          </ShortcutsProvider>
        </MotionRoot>
      </body>
    </html>
  );
}
