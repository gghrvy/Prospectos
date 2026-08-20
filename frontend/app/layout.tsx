import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";

import { Nav } from "@/components/nav";

import "./globals.css";

// A genuinely paired type system (IBM designed these together) rather than
// reaching for Inter: Plex Sans carries prose, Plex Mono carries every
// number/label/data readout — the "diagnostic instrument" identity that
// runs through the whole app (see components/ui/badge.tsx SignalMeter).
const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ProspectOS",
  description: "Internal sales opportunity intelligence dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${plexSans.variable} ${plexMono.variable}`}>
      <body>
        <Nav />
        <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
      </body>
    </html>
  );
}
