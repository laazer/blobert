import type { CSSProperties } from "react";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_NEUTRAL_ACCENT,
  STUDIO_SURFACE_PANEL,
} from "../../styles/studioTokens";

export const STUDIO_VERSION_LIST_GAP_PX = 12;
export const STUDIO_VERSION_ROW_GAP_PX = 6;
export const STUDIO_COMPARE_MAX = 4;

export function studioFilterChipStyle(active: boolean): CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 5,
    background: active ? "#23232e" : "transparent",
    border: "1px solid rgba(255,255,255,0.06)",
    color: active ? STUDIO_INK_PRIMARY : "#8a8a96",
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
  };
}

export function studioSoftButtonStyle(active = false): CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 5,
    background: active ? "rgba(124,140,245,0.18)" : "transparent",
    border: active ? `1px solid ${STUDIO_NEUTRAL_ACCENT}` : "1px solid rgba(255,255,255,0.06)",
    color: active ? "#cdd3ff" : STUDIO_INK_SECONDARY,
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
  };
}

export const studioCompareBarStyle: CSSProperties = {
  padding: "8px 10px",
  borderRadius: 8,
  background: "rgba(124,140,245,0.10)",
  border: "1px solid rgba(124,140,245,0.3)",
  display: "flex",
  alignItems: "center",
  gap: 8,
};

export function studioVersionCardStyle(args: {
  active: boolean;
  inCompare: boolean;
  accentHue: string;
}): CSSProperties {
  const { active, inCompare, accentHue } = args;
  let border = "1px solid rgba(255,255,255,0.04)";
  if (active) border = `1px solid color-mix(in srgb, ${accentHue} 38%, transparent)`;
  else if (inCompare) border = `1px solid color-mix(in srgb, ${STUDIO_NEUTRAL_ACCENT} 50%, transparent)`;

  return {
    padding: "8px 10px",
    borderRadius: 8,
    background: active ? "#1a1a24" : STUDIO_SURFACE_PANEL,
    border,
    position: "relative",
  };
}

export const studioVersionMetaMono: CSSProperties = {
  fontSize: 10,
  color: "#6a6a76",
  marginTop: 2,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
};

export const studioAddTagButtonStyle: CSSProperties = {
  padding: "1px 7px",
  borderRadius: 4,
  background: "transparent",
  border: "1px dashed rgba(255,255,255,0.16)",
  color: "#8a8a96",
  cursor: "pointer",
  fontSize: 10,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  fontWeight: 600,
  display: "inline-flex",
  alignItems: "center",
  gap: 3,
};
