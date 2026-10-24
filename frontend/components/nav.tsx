"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Compass, LayoutDashboard, Send, Users } from "lucide-react";

import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";

const LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/prospects", label: "Prospects", icon: Users },
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/outreach", label: "Outreach", icon: Send },
];

export function Nav() {
  const pathname = usePathname();
  const [gmailConnected, setGmailConnected] = useState<boolean | null>(null);

  useEffect(() => {
    if (isDemoMode) {
      setGmailConnected(false);
      return;
    }
    api.gmailStatus().then((status) => setGmailConnected(status.connected)).catch(() => setGmailConnected(false));
  }, []);

  return (
    <header className="sticky top-0 z-10 border-b border-border/80 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center gap-8 px-5 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-signal text-slate-950">
            <Compass size={15} strokeWidth={2.5} />
          </span>
          <span className="text-sm font-semibold tracking-tight">
            ProspectOS
          </span>
        </Link>
        <nav className="flex gap-1">
          {LINKS.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname?.startsWith(link.href);
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/[.045] hover:text-foreground",
                  active && "bg-white/[.07] font-medium text-foreground"
                )}
              >
                <Icon size={15} className={active ? "text-signal" : ""} />
                {link.label}
              </Link>
            );
          })}
        </nav>
        {isDemoMode ? (
          <span className="ml-auto hidden rounded-full border border-signal/40 bg-signal/10 px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-wider text-signal sm:block">Demo mode</span>
        ) : (
          <span className="ml-auto hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex"><span className={cn("h-1.5 w-1.5 rounded-full", gmailConnected ? "bg-emerald-400" : "bg-muted-foreground/60")} />{gmailConnected ? "Gmail connected" : "Gmail not connected"}</span>
        )}
      </div>
    </header>
  );
}
