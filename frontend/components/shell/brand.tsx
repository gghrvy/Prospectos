import Link from "next/link";

// The mark is a surveyor's benchmark: a ring with a level line through it,
// the symbol stamped on maps where a measured reference point was set.
export function Brand() {
  return (
    <Link href="/" className="focus-ring -mx-1 inline-flex items-center gap-2.5 rounded-control px-1 py-1">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" className="text-survey">
        <circle cx="11" cy="11" r="8.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M1.5 11h19" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="11" cy="11" r="2.25" fill="currentColor" />
      </svg>
      <span className="font-serif text-[17px] font-semibold tracking-[-0.01em] text-ink">ProspectOS</span>
    </Link>
  );
}
