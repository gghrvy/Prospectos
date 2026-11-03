"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Keyboard } from "lucide-react";

import { Brand } from "@/components/shell/brand";
import { isActive, NAV_ITEMS } from "@/components/shell/nav-items";
import { useShortcutsHelp } from "@/components/shell/shortcuts";
import { api } from "@/lib/api";
import { isDemoMode } from "@/lib/runtime";
import { cn } from "@/lib/utils";

export function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Main">
      <ul className="flex flex-col gap-0.5">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item.href, pathname);
          const Icon = item.icon;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "focus-ring relative flex h-9 items-center gap-2.5 rounded-control px-3 text-sm transition-colors duration-fast ease-assay",
                  active ? "bg-survey/[0.08] font-medium text-survey" : "text-graphite hover:bg-ink/[0.04] hover:text-ink"
                )}
              >
                {active && <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-survey" aria-hidden="true" />}
                <Icon size={16} strokeWidth={1.75} aria-hidden="true" />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function ConnectionStatus() {
  const [gmailConnected, setGmailConnected] = useState<boolean | null>(null);

  useEffect(() => {
    if (isDemoMode) return;
    api.gmailStatus().then((status) => setGmailConnected(status.connected)).catch(() => setGmailConnected(false));
  }, []);

  if (isDemoMode) {
    return <p className="px-3 text-xs text-graphite">Public demo with sample data</p>;
  }
  return (
    <p className="flex items-center gap-2 px-3 text-xs text-graphite">
      <span
        className={cn("h-2 w-2 rounded-full", gmailConnected ? "bg-survey" : "border border-graphite/60")}
        aria-hidden="true"
      />
      {gmailConnected === null ? "Checking Gmail" : gmailConnected ? "Gmail connected" : "Gmail not connected"}
    </p>
  );
}

export function ShortcutsButton() {
  const openHelp = useShortcutsHelp();
  return (
    <button
      type="button"
      onClick={openHelp}
      className="focus-ring flex h-8 w-full items-center gap-2.5 rounded-control px-3 text-xs text-graphite transition-colors duration-fast ease-assay hover:bg-ink/[0.04] hover:text-ink"
    >
      <Keyboard size={15} strokeWidth={1.75} aria-hidden="true" />
      Keyboard shortcuts
      <span className="ml-auto text-graphite/80">?</span>
    </button>
  );
}

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh w-56 shrink-0 flex-col border-r border-rule bg-paper px-3 py-5 lg:flex">
      <div className="px-2">
        <Brand />
      </div>
      <div className="mt-8 flex-1">
        <NavList />
      </div>
      <div className="flex flex-col gap-3 border-t border-rule pt-4">
        <ConnectionStatus />
        <ShortcutsButton />
      </div>
    </aside>
  );
}
