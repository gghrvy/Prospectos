"use client";

import { type ReactNode, useEffect, useLayoutEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { DURATION, exit } from "@/lib/motion";
import { cn } from "@/lib/utils";

// Built on the native <dialog>: showModal() gives focus containment, Esc to
// close and an inert background without extra code. Focus returns to the
// element that opened it. Closing keeps the dialog open for the exit
// animation (globals.css, .assay-dialog / .assay-drawer) and then closes it.
export function Dialog({
  open,
  onClose,
  title,
  children,
  className,
  variant = "center",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
  variant?: "center" | "drawer";
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog || !open) return;
    // Reopened mid-exit: the dialog never closed, so only cancel the exit.
    setClosing(false);
    if (dialog.open) return;
    returnFocus.current = document.activeElement as HTMLElement | null;
    dialog.showModal();
    // showModal() focuses the first control (the close button); let content
    // name a better starting point, e.g. Cancel on a destructive confirm.
    dialog.querySelector<HTMLElement>("[data-autofocus]")?.focus();
  }, [open]);

  // A layout effect, so the frame between "open went false" and "closing
  // went true" is never painted without content.
  useLayoutEffect(() => {
    const dialog = ref.current;
    if (!dialog || open || !dialog.open) return;
    const finish = () => {
      dialog.close();
      setClosing(false);
      returnFocus.current?.focus();
    };
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      finish();
      return;
    }
    setClosing(true);
    const handle = setTimeout(finish, exit(variant === "drawer" ? DURATION.slow : DURATION.base) * 1000);
    return () => clearTimeout(handle);
  }, [open, variant]);

  return (
    <dialog
      ref={ref}
      aria-label={title}
      data-closing={closing || undefined}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        // A click on the backdrop lands on the <dialog> element itself.
        if (event.target === ref.current) onClose();
      }}
      className={cn(
        "m-0 max-h-none max-w-none border-rule bg-sheet p-0 text-ink shadow-float backdrop:bg-ink/30",
        variant === "center" && "assay-dialog fixed inset-0 m-auto h-fit w-[min(28rem,calc(100vw-2rem))] rounded-panel border",
        variant === "drawer" && "assay-drawer fixed inset-y-0 left-0 h-dvh w-72 max-w-[85vw] border-r",
        className
      )}
    >
      {(open || closing) && (
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between gap-4 border-b border-rule px-4 py-3">
            <h2 className="text-base font-semibold">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="focus-ring -mr-1 inline-flex h-8 w-8 items-center justify-center rounded-control text-graphite transition-colors duration-fast ease-assay hover:bg-ink/[0.05] hover:text-ink"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
        </div>
      )}
    </dialog>
  );
}
