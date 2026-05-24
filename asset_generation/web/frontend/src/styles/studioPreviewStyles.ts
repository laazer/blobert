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

export const studioPreviewMetaBarRoot: CSSProperties = {
  flexShrink: 0,
  display: "flex",
  flexWrap: "wrap",
  alignItems: "center",
  gap: 6,
  padding: "8px 12px",
  background: "#0d0d13",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  minHeight: 0,
};

const studioPreviewMetaChipBase: CSSProperties = {
  flex: "0 1 auto",
  padding: "4px 10px",
  borderRadius: 6,
  border: "1px solid rgba(255,255,255,0.1)",
  background: "rgba(255,255,255,0.03)",
  fontSize: 12,
  maxWidth: "min(100%, 420px)",
};

/** Read-only GLB / version id chip (monospace). */
export const studioPreviewMetaFileChip: CSSProperties = {
  ...studioPreviewMetaChipBase,
  color: STUDIO_INK_SECONDARY,
  fontWeight: 500,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  flexShrink: 0,
};

/** Editable registry display name. */
export const studioPreviewMetaNameChip: CSSProperties = {
  ...studioPreviewMetaChipBase,
  minWidth: 96,
  color: STUDIO_INK_PRIMARY,
  fontWeight: 600,
  fontFamily: "inherit",
  outline: "none",
};

export function studioPreviewSizeChipStyle(inert: boolean): CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 6,
    border: "1px solid rgba(255,255,255,0.1)",
    background: inert ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.06)",
    color: inert ? STUDIO_INK_SECONDARY : STUDIO_INK_PRIMARY,
    fontSize: 12,
    fontWeight: 600,
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
    cursor: inert ? "default" : "pointer",
    lineHeight: 1.2,
    minWidth: 32,
    textAlign: "center",
  };
}

const STUDIO_PREVIEW_VIEWPORT_BASE = "#08080c";
const STUDIO_PREVIEW_VIEWPORT_EDGE = "#040406";

/** Radial wash behind the GLB viewer — muted glow at center, very dark at edges. */
export function studioPreviewViewportGlowBackground(accentHue: string): string {
  const glowCore = `color-mix(in srgb, ${accentHue} 8%, ${STUDIO_PREVIEW_VIEWPORT_BASE})`;
  const glowMid = `color-mix(in srgb, ${accentHue} 3%, ${STUDIO_PREVIEW_VIEWPORT_BASE})`;
  return [
    `radial-gradient(ellipse 58% 52% at 50% 46%, ${glowCore} 0%, transparent 52%)`,
    `radial-gradient(ellipse 92% 84% at 50% 50%, ${glowMid} 0%, ${STUDIO_PREVIEW_VIEWPORT_EDGE} 100%)`,
    STUDIO_PREVIEW_VIEWPORT_EDGE,
  ].join(", ");
}

export function studioPreviewViewportFrameStyle(accentHue: string): CSSProperties {
  return {
    flex: 1,
    minHeight: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: studioPreviewViewportGlowBackground(accentHue),
    overflow: "hidden",
  };
}

export function studioPreviewViewportShellStyle(accentHue: string): CSSProperties {
  return {
    boxShadow: [
      `0 0 40px color-mix(in srgb, ${accentHue} 11%, transparent)`,
      `0 0 88px color-mix(in srgb, ${accentHue} 4%, transparent)`,
      "inset 0 0 64px rgba(0, 0, 0, 0.55)",
    ].join(", "),
  };
}
