import { ImageResponse } from "next/og";

// The link preview for the public demo: the benchmark mark, the product's one
// line, and the four steps it runs. Token colors from MASTER.md, written as
// hex because ImageResponse can't read CSS variables.
export const alt = "ProspectOS finds local businesses, audits their websites and drafts outreach for approval.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
// The edge build of next/og bundles its font; the Node build resolves it from a
// file URL that breaks on Windows paths (local builds fail with "Invalid URL").
export const runtime = "edge";

const PAPER = "#F3F2EE";
const INK = "#1C1F1D";
const GRAPHITE = "#5E625D";
const RULE = "#D9D7D0";
const SURVEY = "#1E5A43";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: PAPER,
          padding: "72px 80px",
          color: INK,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <svg width="52" height="52" viewBox="0 0 22 22">
            <circle cx="11" cy="11" r="8.25" fill="none" stroke={SURVEY} strokeWidth="1.5" />
            <path d="M1.5 11h19" stroke={SURVEY} strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="11" cy="11" r="2.25" fill={SURVEY} />
          </svg>
          <span style={{ fontSize: 40, fontWeight: 600, letterSpacing: "-0.01em" }}>ProspectOS</span>
        </div>
        <div style={{ display: "flex", fontSize: 64, lineHeight: 1.12, letterSpacing: "-0.02em", maxWidth: 940 }}>
          Find the local businesses a better website would help most.
        </div>
        <div style={{ display: "flex", gap: 40, borderTop: `2px solid ${RULE}`, paddingTop: 28, fontSize: 28, color: GRAPHITE }}>
          <span>Discover</span>
          <span>Audit</span>
          <span>Score</span>
          <span style={{ color: SURVEY }}>Draft for approval</span>
        </div>
      </div>
    ),
    size
  );
}
