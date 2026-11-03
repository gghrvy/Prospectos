"use client";

import { createContext, forwardRef, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

import { DURATION, exit } from "@/lib/motion";
import { cn } from "@/lib/utils";

type Tone = "success" | "error";
type Toast = (message: string, tone?: Tone) => void;

interface Item {
  id: number;
  message: string;
  tone: Tone;
}

const ToastContext = createContext<Toast | null>(null);
const LIFETIME = 4000;
const MAX = 3;

// Short results of an action ("Saved 3 leads."), announced politely and
// gone after four seconds. Never takes focus. Errors that block the page use
// ErrorState instead.
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Item[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => setItems((current) => current.filter((item) => item.id !== id)), []);

  const toast = useCallback<Toast>((message, tone = "success") => {
    const id = nextId.current++;
    setItems((current) => [...current.slice(-(MAX - 1)), { id, message, tone }]);
  }, []);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        aria-live="polite"
        aria-relevant="additions"
        className="pointer-events-none fixed inset-x-4 top-16 z-[60] flex flex-col gap-2 sm:bottom-4 sm:left-auto sm:top-auto sm:w-[360px]"
      >
        <AnimatePresence mode="popLayout" initial={false}>
          {items.map((item) => (
            <ToastItem key={item.id} item={item} onDismiss={dismiss} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

// forwardRef because popLayout measures the exiting toast through its ref.
const ToastItem = forwardRef<HTMLDivElement, { item: Item; onDismiss: (id: number) => void }>(function ToastItem(
  { item, onDismiss },
  ref
) {
  const [paused, setPaused] = useState(false);

  // Hovering or focusing the toast holds it open so it can be read.
  useEffect(() => {
    if (paused) return;
    const handle = setTimeout(() => onDismiss(item.id), LIFETIME);
    return () => clearTimeout(handle);
  }, [paused, item.id, onDismiss]);

  return (
    <motion.div
      ref={ref}
      layout
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1, transition: { duration: DURATION.base } }}
      exit={{ opacity: 0, transition: { duration: exit(DURATION.base) } }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      className="pointer-events-auto flex items-start gap-3 rounded-panel border border-rule bg-sheet py-2.5 pl-4 pr-2 text-sm text-ink shadow-float"
    >
      <span
        aria-hidden="true"
        className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", item.tone === "error" ? "bg-brick" : "bg-ink")}
      />
      <p className="flex-1 leading-5">
        {item.tone === "error" && <span className="sr-only">Error: </span>}
        {item.message}
      </p>
      <button
        type="button"
        onClick={() => onDismiss(item.id)}
        aria-label="Dismiss"
        className="focus-ring -my-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-control text-graphite hover:bg-ink/[0.05] hover:text-ink"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </motion.div>
  );
});

export function useToast(): Toast {
  const toast = useContext(ToastContext);
  if (!toast) throw new Error("useToast must be used inside <ToastProvider>");
  return toast;
}
