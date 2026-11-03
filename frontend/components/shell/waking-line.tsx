"use client";

import { useEffect, useState } from "react";

import { subscribePendingRequests } from "@/lib/api";

const WAKING_AFTER_MS = 5000;

// Shown under the demo notice when requests have been waiting a while: the
// demo's free server sleeps when idle and takes up to a minute to wake.
export function WakingLine() {
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const unsubscribe = subscribePendingRequests((count) => {
      if (count === 0) {
        clearTimeout(timer);
        timer = undefined;
        setWaking(false);
      } else if (timer === undefined) {
        timer = setTimeout(() => setWaking(true), WAKING_AFTER_MS);
      }
    });
    return () => {
      clearTimeout(timer);
      unsubscribe();
    };
  }, []);

  return (
    <span role="status" className="block text-graphite">
      {waking && "Waking the demo server. The first load after a quiet spell can take up to a minute."}
    </span>
  );
}
