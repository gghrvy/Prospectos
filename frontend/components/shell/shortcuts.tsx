"use client";

import { useRouter } from "next/navigation";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";

import { NAV_ITEMS } from "@/components/shell/nav-items";
import { Dialog } from "@/components/ui/dialog";

type Handler = () => void;

interface ShortcutsContextValue {
  register: (key: string, handler: Handler) => () => void;
  openHelp: () => void;
}

const ShortcutsContext = createContext<ShortcutsContextValue | null>(null);

// Keys are ignored while the person is typing, and whenever a modifier is
// held, so browser and OS shortcuts (Ctrl+F, Cmd+L...) keep working.
function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(target.closest("input, textarea, select, [contenteditable=''], [contenteditable='true']"));
}

function isActivatable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(target.closest("a[href], button, summary, [role='button'], [role^='menuitem']"));
}

const CHORD_TIMEOUT_MS = 1000;

const PAGE_SHORTCUTS: { keys: string[]; label: string }[] = [
  { keys: ["/"], label: "Search leads" },
  { keys: ["j"], label: "Next row" },
  { keys: ["k"], label: "Previous row" },
  { keys: ["Enter"], label: "Open highlighted row" },
  { keys: ["x"], label: "Select highlighted row" },
];

export function ShortcutsProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const handlers = useRef(new Map<string, Handler>());
  const chordStarted = useRef<number | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);

  const register = useCallback((key: string, handler: Handler) => {
    handlers.current.set(key, handler);
    return () => {
      if (handlers.current.get(key) === handler) handlers.current.delete(key);
    };
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
      if (isEditable(event.target)) return;
      // Enter and Space already activate the focused button or link.
      if ((event.key === "Enter" || event.key === " ") && isActivatable(event.target)) return;
      if (document.querySelector("dialog[open]") && event.key !== "?") return;

      const now = Date.now();
      if (chordStarted.current !== null && now - chordStarted.current < CHORD_TIMEOUT_MS) {
        chordStarted.current = null;
        const target = NAV_ITEMS.find((item) => item.key === event.key.toLowerCase());
        if (target) {
          event.preventDefault();
          router.push(target.href);
        }
        return;
      }
      chordStarted.current = null;

      if (event.key === "g") {
        chordStarted.current = now;
        return;
      }
      if (event.key === "?") {
        event.preventDefault();
        setHelpOpen((open) => !open);
        return;
      }
      const handler = handlers.current.get(event.key);
      if (handler) {
        event.preventDefault();
        handler();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  return (
    <ShortcutsContext.Provider value={{ register, openHelp: () => setHelpOpen(true) }}>
      {children}
      <Dialog open={helpOpen} onClose={() => setHelpOpen(false)} title="Keyboard shortcuts">
        <div className="grid gap-5 p-4 text-sm">
          <ShortcutGroup
            title="Go to"
            rows={NAV_ITEMS.map((item) => ({ keys: ["g", item.key], label: item.label }))}
          />
          <ShortcutGroup title="In lists" rows={PAGE_SHORTCUTS} />
          <ShortcutGroup title="Anywhere" rows={[{ keys: ["?"], label: "Show or hide this list" }]} />
        </div>
      </Dialog>
    </ShortcutsContext.Provider>
  );
}

function ShortcutGroup({ title, rows }: { title: string; rows: { keys: string[]; label: string }[] }) {
  return (
    <section>
      <h3 className="mb-2 text-xs font-medium text-graphite">{title}</h3>
      <dl className="divide-y divide-rule/70">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between py-1.5">
            <dt>{row.label}</dt>
            <dd className="flex gap-1">
              {row.keys.map((key, index) => (
                <span key={index} className="flex items-center gap-1">
                  {index > 0 && <span className="text-xs text-graphite">then</span>}
                  <Kbd>{key}</Kbd>
                </span>
              ))}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="inline-flex h-6 min-w-6 items-center justify-center rounded-tag border border-rule bg-paper px-1.5 font-sans text-xs text-ink">
      {children}
    </kbd>
  );
}

export function useShortcutsHelp(): () => void {
  const context = useContext(ShortcutsContext);
  return context?.openHelp ?? (() => {});
}

// Registers a single-key page shortcut for the lifetime of the component.
export function useShortcut(key: string, handler: Handler, enabled = true) {
  const context = useContext(ShortcutsContext);
  const latest = useRef(handler);
  latest.current = handler;

  useEffect(() => {
    if (!context || !enabled) return;
    return context.register(key, () => latest.current());
  }, [context, key, enabled]);
}
