"use client";

import { useState } from "react";
import { Menu } from "lucide-react";

import { Brand } from "@/components/shell/brand";
import { ConnectionStatus, NavList } from "@/components/shell/sidebar";
import { Dialog } from "@/components/ui/dialog";

// Below 1024px the sidebar becomes a top bar with a slide-in drawer.
export function MobileBar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-rule bg-paper/95 px-4 backdrop-blur lg:hidden">
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-expanded={open}
        className="focus-ring -ml-2 inline-flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-fast ease-assay hover:bg-ink/[0.05]"
      >
        <Menu size={20} strokeWidth={1.75} aria-hidden="true" />
      </button>
      <Brand />
      <Dialog open={open} onClose={() => setOpen(false)} title="Navigation" variant="drawer">
        <div className="flex h-full flex-col gap-6 p-3">
          <NavList onNavigate={() => setOpen(false)} />
          <div className="mt-auto border-t border-rule pt-4">
            <ConnectionStatus />
          </div>
        </div>
      </Dialog>
    </header>
  );
}
