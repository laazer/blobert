import type { CSSProperties } from "react";

export const STUDIO_SURFACE_ROOT = "#0c0c10";
export const STUDIO_SURFACE_BAR = "#0e0e14";
export const STUDIO_SURFACE_PANEL = "#16161d";

export const STUDIO_INK_PRIMARY = "#ededf0";
export const STUDIO_INK_SECONDARY = "#bababf";
export const STUDIO_INK_MUTED = "#7a7a86";

export const STUDIO_LIBRARY_WIDTH_PX = 256;
export const STUDIO_INSPECTOR_WIDTH_PX = 360;
export const STUDIO_TOP_BAR_HEIGHT_PX = 52;

export const STUDIO_NEUTRAL_ACCENT = "#7c8cf5";

const studioInspectorTabBase: CSSProperties = {
  flex: 1,
  padding: "10px 4px",
  fontSize: 11,
  fontWeight: 600,
  border: "none",
  borderBottom: "2px solid transparent",
  background: "transparent",
  cursor: "pointer",
  color: STUDIO_INK_MUTED,
};

/** Inspector tab strip — active underline uses element hue when provided. */
export function studioInspectorTabStyle(active: boolean, elementHue?: string): CSSProperties {
  const accent = elementHue ?? STUDIO_NEUTRAL_ACCENT;
  return {
    ...studioInspectorTabBase,
    color: active ? STUDIO_INK_PRIMARY : STUDIO_INK_MUTED,
    borderBottomColor: active ? accent : "transparent",
  };
}

export const studioLayoutRootStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: `${STUDIO_LIBRARY_WIDTH_PX}px 1fr ${STUDIO_INSPECTOR_WIDTH_PX}px`,
  gridTemplateRows: `${STUDIO_TOP_BAR_HEIGHT_PX}px 1fr`,
  height: "100vh",
  overflow: "hidden",
  background: STUDIO_SURFACE_ROOT,
  color: STUDIO_INK_PRIMARY,
};
