import type { CSSProperties } from "react";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY, STUDIO_INK_SECONDARY, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";

export const studioBuildRowLabel: CSSProperties = {
  flexShrink: 0,
  minWidth: 88,
  fontSize: 12,
  color: "#bababf",
  fontWeight: 500,
};

/** Count / long segmented rows: label above pills (avoids clipping in narrow inspector). */
export const studioBuildRowStacked: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "stretch",
  gap: 6,
};

export const studioBuildRowGap: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
};

export const studioBuildSegmentTrack: CSSProperties = {
  display: "flex",
  gap: 3,
  background: STUDIO_SURFACE_PANEL,
  padding: 3,
  borderRadius: 6,
  flexShrink: 0,
};

export const studioBuildSegmentWrapTrack: CSSProperties = {
  ...studioBuildSegmentTrack,
  flexWrap: "wrap",
  flex: 1,
  minWidth: 0,
};

export function studioBuildSegmentButton(active: boolean, accentHue: string): CSSProperties {
  return {
    padding: "4px 8px",
    border: 0,
    background: active ? accentHue : "transparent",
    color: active ? "#0c0c10" : "#8a8a96",
    fontSize: 11,
    fontWeight: 600,
    borderRadius: 4,
    cursor: "pointer",
    fontFamily: "inherit",
    whiteSpace: "nowrap",
  };
}

export const studioBuildFilterInput: CSSProperties = {
  background: "#121218",
  color: STUDIO_INK_SECONDARY,
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "4px 8px",
  fontSize: 11,
  width: "100%",
  maxWidth: 200,
  marginBottom: 10,
};

export const studioBuildSliderValue: CSSProperties = {
  fontSize: 11,
  color: STUDIO_INK_MUTED,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
};

export const studioBuildSliderLabel: CSSProperties = {
  fontSize: 11,
  color: STUDIO_INK_SECONDARY,
  fontWeight: 500,
};
