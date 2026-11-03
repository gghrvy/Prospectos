// The dashboard's average-opportunity dial: a 270-degree sweep like an analog
// meter, drawn in survey green on a rule-colored track.
const SIZE = 176;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const SWEEP_DEG = 270;
const START_DEG = 135; // rotate so the gap sits at the bottom

export function RadialGauge({ score, label }: { score: number | null; label: string }) {
  const clamped = score === null ? 0 : Math.max(0, Math.min(100, score));
  const sweepLength = (CIRCUMFERENCE * SWEEP_DEG) / 360;
  const filledLength = (sweepLength * clamped) / 100;

  return (
    <div
      className="relative flex shrink-0 items-center justify-center"
      style={{ width: SIZE, height: SIZE }}
      role="img"
      aria-label={score === null ? `${label}: no audits yet` : `${label}: ${score} of 100`}
    >
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="absolute inset-0"
        style={{ transform: `rotate(${START_DEG}deg)` }}
        aria-hidden="true"
      >
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          className="stroke-rule"
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
            className="stroke-survey"
            strokeWidth={STROKE}
            strokeDasharray={`${filledLength} ${CIRCUMFERENCE}`}
            strokeLinecap="round"
          />
        )}
      </svg>
      <div className="relative flex flex-col items-center" aria-hidden="true">
        <span className="font-serif text-[40px] font-medium leading-none tabular-nums text-ink">{score ?? "–"}</span>
        <span className="mt-2 max-w-[8rem] text-center text-xs text-graphite">{label}</span>
      </div>
    </div>
  );
}
