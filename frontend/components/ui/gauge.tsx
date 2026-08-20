// The dashboard's dominant hero: a radial gauge dial rather than a stat
// box, because this app's whole job is reading a signal off a dark
// backdrop -- an instrument dial says that in one glance in a way a
// number in a rounded rectangle never will.
const SIZE = 200;
const STROKE = 12;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
// A 270-degree sweep (like an analog meter), not a full circle -- leaves
// the open bottom third as the "dead zone" a real gauge always has.
const SWEEP_DEG = 270;
const START_DEG = 135; // rotate so the gap sits at the bottom

function arcColor(score: number): string {
  if (score >= 70) return "#34D399";
  if (score >= 40) return "#FBBF24";
  return "#F87171";
}

export function RadialGauge({
  score,
  label,
}: {
  score: number | null;
  label: string;
}) {
  const clamped = score === null ? 0 : Math.max(0, Math.min(100, score));
  const sweepLength = (CIRCUMFERENCE * SWEEP_DEG) / 360;
  const filledLength = (sweepLength * clamped) / 100;
  const color = score === null ? "hsl(var(--line))" : arcColor(clamped);

  return (
    <div className="relative flex items-center justify-center" style={{ width: SIZE, height: SIZE }}>
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="absolute inset-0"
        style={{ transform: `rotate(${START_DEG}deg)` }}
      >
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="hsl(var(--line))"
          strokeWidth={STROKE}
          strokeDasharray={`${sweepLength} ${CIRCUMFERENCE}`}
          strokeLinecap="round"
        />
        {score !== null && (
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeDasharray={`${filledLength} ${CIRCUMFERENCE}`}
            strokeLinecap="round"
            style={{ transition: "stroke-dasharray 300ms ease-out" }}
          />
        )}
      </svg>
      <div className="relative flex flex-col items-center">
        <span className="font-mono text-5xl font-semibold tabular-nums tracking-tight" style={{ color }}>
          {score ?? "--"}
        </span>
        <span className="mt-1 max-w-[10rem] text-center font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
      </div>
    </div>
  );
}
