import type { CSSProperties } from "react";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_PANEL,
} from "./studioTokens";

export const studioAnimationPanelRoot: CSSProperties = {
  background: "#0d0d13",
  borderTop: "1px solid rgba(255,255,255,0.06)",
  padding: "10px 16px",
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
  alignItems: "center",
};

export const studioAnimationCollapsibleBar: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  padding: "8px 16px",
  background: "#0d0d13",
  borderTop: "1px solid rgba(255,255,255,0.06)",
  flexShrink: 0,
};

export const studioAnimationCollapsibleTitle: CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: STUDIO_INK_MUTED,
  flex: 1,
};

export function studioAnimationClipButton(active: boolean, accentHue: string): CSSProperties {
  return {
    padding: "5px 10px",
    borderRadius: 6,
    background: active ? accentHue : STUDIO_SURFACE_PANEL,
    color: active ? "#0c0c10" : STUDIO_INK_SECONDARY,
    border: active ? "none" : "1px solid rgba(255,255,255,0.06)",
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
    whiteSpace: "nowrap",
  };
}

export function studioAnimationPauseButton(paused: boolean, accentHue: string): CSSProperties {
  return {
    padding: "5px 12px",
    borderRadius: 6,
    background: paused ? STUDIO_SURFACE_PANEL : accentHue,
    color: paused ? STUDIO_INK_PRIMARY : "#0c0c10",
    border: paused ? "1px solid rgba(255,255,255,0.06)" : "none",
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  };
}

export const studioAnimationCollapsibleToggle: CSSProperties = {
  background: STUDIO_SURFACE_PANEL,
  color: STUDIO_INK_SECONDARY,
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "4px 10px",
  cursor: "pointer",
  fontSize: 11,
  fontWeight: 600,
  fontFamily: "inherit",
};
