import type { CSSProperties } from "react";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY } from "../../styles/studioTokens";

export const studioFillRootStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
  padding: 0,
};

export const studioFillTabBarStyle: CSSProperties = {
  display: "flex",
  gap: 0,
  background: "#16161d",
  padding: 3,
  borderRadius: 7,
};

export const studioFillContentStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

export function studioFillPanelStyle(embedded: boolean | undefined): CSSProperties {
  return {
    background: embedded ? "#0a0a10" : "transparent",
    borderRadius: embedded ? 10 : 0,
    padding: embedded ? 12 : 0,
    border: embedded ? "1px solid rgba(255,255,255,0.04)" : "none",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  };
}

export const studioLabelCaps: CSSProperties = {
  fontSize: 9,
  color: STUDIO_INK_MUTED,
  fontWeight: 600,
  letterSpacing: 0.5,
  textTransform: "uppercase",
  marginBottom: 4,
};

export const studioChipButtonStyle: CSSProperties = {
  fontSize: 10,
  color: STUDIO_INK_MUTED,
  background: "transparent",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 4,
  padding: "2px 7px",
  cursor: "pointer",
  fontFamily: "var(--font-mono, monospace)",
  fontWeight: 600,
};

export function studioPillStyle(active: boolean): CSSProperties {
  return {
    flex: 1,
    padding: "4px 0",
    borderRadius: 5,
    border: "1px solid rgba(255,255,255,0.06)",
    background: active ? "#23232e" : "transparent",
    color: active ? STUDIO_INK_PRIMARY : "#8a8a96",
    fontSize: 10,
    fontWeight: 600,
    cursor: "pointer",
  };
}

export function studioFillTabStyle(active: boolean, accentHue: string): CSSProperties {
  return {
    flex: 1,
    padding: "6px 8px",
    border: "none",
    background: active ? accentHue : "transparent",
    color: active ? "#0c0c10" : "#8a8a96",
    borderRadius: 5,
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 0.1,
  };
}
