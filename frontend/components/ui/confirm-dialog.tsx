"use client";

import { createContext, type ReactNode, useCallback, useContext, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

interface ConfirmOptions {
  title: string;
  body: string;
  confirmLabel: string;
  tone?: "danger";
}

type Confirm = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmContext = createContext<Confirm | null>(null);

// Replaces window.confirm() with an in-app dialog that names the action on
// its button. For destructive actions, Cancel takes initial focus so Enter
// can't delete by accident.
export function ConfirmProvider({ children }: { children: ReactNode }) {
  // Options outlive "open" so the dialog keeps its text while it animates out.
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const [open, setOpen] = useState(false);
  const resolver = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback<Confirm>((next) => {
    resolver.current?.(false);
    setOptions(next);
    setOpen(true);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  function settle(value: boolean) {
    resolver.current?.(value);
    resolver.current = null;
    setOpen(false);
  }

  const danger = options?.tone === "danger";

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <Dialog open={open} onClose={() => settle(false)} title={options?.title ?? ""}>
        {options && (
          <div className="flex flex-col gap-5 p-4">
            <p className="text-sm leading-6 text-graphite">{options.body}</p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" data-autofocus={danger || undefined} onClick={() => settle(false)}>
                Cancel
              </Button>
              <Button variant={danger ? "destructive" : "default"} data-autofocus={!danger || undefined} onClick={() => settle(true)}>
                {options.confirmLabel}
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </ConfirmContext.Provider>
  );
}

export function useConfirm(): Confirm {
  const confirm = useContext(ConfirmContext);
  if (!confirm) throw new Error("useConfirm must be used inside <ConfirmProvider>");
  return confirm;
}
