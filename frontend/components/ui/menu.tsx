"use client";

import { type ReactNode, useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Check, MoreHorizontal } from "lucide-react";

import { DURATION, exit } from "@/lib/motion";
import { cn } from "@/lib/utils";

export interface MenuItem {
  label: string;
  onSelect: () => void;
  tone?: "danger";
  checked?: boolean;
  disabled?: boolean;
}

const WIDTH = 192;
const MAX_HEIGHT = 360;

// A small action menu. It renders in a portal with fixed positioning so a
// scrolling table can't clip it. Arrow keys, Home/End move; Esc, Tab and an
// outside click close it; focus goes back to the button.
export function Menu({
  label,
  items,
  trigger,
  icon,
  className,
}: {
  label: string;
  items: MenuItem[];
  // Visible text trigger; without it the button is an icon labelled by `label`.
  trigger?: ReactNode;
  icon?: ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number; below: boolean } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  // The portal target only exists in the browser.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const menuId = useId();

  const close = useCallback((refocus = true) => {
    setOpen(false);
    if (refocus) buttonRef.current?.focus();
  }, []);

  useLayoutEffect(() => {
    if (!open || !buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const height = Math.min(items.length * 36 + 8, MAX_HEIGHT);
    const below = rect.bottom + 4 + height <= window.innerHeight;
    setPosition({
      top: below ? rect.bottom + 4 : Math.max(8, rect.top - 4 - height),
      left: Math.min(Math.max(8, rect.right - WIDTH), window.innerWidth - WIDTH - 8),
      below,
    });
  }, [open, items.length]);

  useEffect(() => {
    if (!open) return;
    menuRef.current?.querySelector<HTMLButtonElement>("[role^=menuitem]:not([disabled])")?.focus();
    function onPointer(event: PointerEvent) {
      const target = event.target as Node;
      if (!menuRef.current?.contains(target) && !buttonRef.current?.contains(target)) close(false);
    }
    // The page scrolling moves the trigger away; the menu's own scroll doesn't.
    const onScroll = (event: Event) => {
      if (event.target instanceof Node && menuRef.current?.contains(event.target)) return;
      close(false);
    };
    document.addEventListener("pointerdown", onPointer);
    window.addEventListener("resize", onScroll);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("resize", onScroll);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open, position, close]);

  function onMenuKeyDown(event: React.KeyboardEvent) {
    const buttons = [...(menuRef.current?.querySelectorAll<HTMLButtonElement>("[role^=menuitem]:not([disabled])") ?? [])];
    const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
    if (event.key === "Tab") {
      close(false);
      return;
    }
    // Swallow every other key so page shortcuts (j, k, x) don't fire underneath.
    if (event.key !== "Enter" && event.key !== " ") event.preventDefault();
    if (event.key === "Escape") close();
    else if (event.key === "ArrowDown") buttons[(index + 1) % buttons.length]?.focus();
    else if (event.key === "ArrowUp") buttons[(index - 1 + buttons.length) % buttons.length]?.focus();
    else if (event.key === "Home") buttons[0]?.focus();
    else if (event.key === "End") buttons[buttons.length - 1]?.focus();
  }

  const hasChecks = items.some((item) => item.checked !== undefined);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        aria-label={trigger ? undefined : label}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" && !open) {
            event.preventDefault();
            setOpen(true);
          }
        }}
        className={cn(
          "focus-ring inline-flex items-center justify-center gap-1.5 rounded-control text-graphite transition-colors duration-fast ease-assay hover:bg-ink/[0.05] hover:text-ink aria-expanded:bg-ink/[0.06] aria-expanded:text-ink",
          trigger ? "h-8 px-2.5 text-[13px]" : "h-8 w-8",
          className
        )}
      >
        {trigger ?? icon ?? <MoreHorizontal size={16} aria-hidden="true" />}
      </button>
      {mounted && createPortal(
        <AnimatePresence>
          {open && position && (
          <motion.div
            key="menu"
            // Set only on mount: an exiting menu must not null the ref of one
            // reopened before its exit finished.
            ref={(el) => {
              if (el) menuRef.current = el;
            }}
            // Grows from the corner nearest its trigger; exits by fading only.
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1, transition: { duration: DURATION.base } }}
            exit={{ opacity: 0, transition: { duration: exit(DURATION.base) } }}
            id={menuId}
            role="menu"
            aria-label={label}
            onKeyDown={onMenuKeyDown}
            style={{
              top: position.top,
              left: position.left,
              width: WIDTH,
              maxHeight: MAX_HEIGHT,
              transformOrigin: position.below ? "top right" : "bottom right",
            }}
            className="fixed z-50 overflow-y-auto overscroll-contain rounded-panel border border-rule bg-sheet p-1 shadow-float"
          >
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                role={item.checked === undefined ? "menuitem" : "menuitemradio"}
                aria-checked={item.checked}
                disabled={item.disabled}
                onClick={() => {
                  close();
                  item.onSelect();
                }}
                className={cn(
                  "flex h-9 w-full items-center gap-2 rounded-control px-2.5 text-left text-sm outline-none transition-colors duration-fast ease-assay focus-visible:bg-ink/[0.06] disabled:opacity-45",
                  item.tone === "danger" ? "text-brick hover:bg-brick/[0.07] focus-visible:bg-brick/[0.07]" : "text-ink hover:bg-ink/[0.05]"
                )}
              >
                {hasChecks && (
                  <span className="w-4 shrink-0 text-survey" aria-hidden="true">
                    {item.checked && <Check size={14} />}
                  </span>
                )}
                {item.label}
              </button>
            ))}
          </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
}
