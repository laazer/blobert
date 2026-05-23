import type { CSSProperties } from "react";

export type PatternTileId = "stripes" | "dots" | "swirl" | "cracks" | "plain";

export type PatternTileDef = {
  id: PatternTileId;
  label: string;
  /** Value written to ``feat_{zone}_texture_mode``. */
  textureMode: string;
};

export const STUDIO_PATTERN_TILES: readonly PatternTileDef[] = [
  { id: "stripes", label: "stripes", textureMode: "stripes" },
  { id: "dots", label: "dots", textureMode: "spots" },
  { id: "swirl", label: "swirl", textureMode: "checkerboard" },
  { id: "cracks", label: "cracks", textureMode: "assets" },
  { id: "plain", label: "plain", textureMode: "none" },
] as const;

/** CSS background for pattern preview tiles (mockup Look tab). */
export function patternTilePreviewStyle(
  tileId: PatternTileId,
  bodyHex: string,
  patternHex: string,
): CSSProperties {
  const base: CSSProperties = {
    flex: 1,
    backgroundColor: bodyHex,
    backgroundSize: tileId === "dots" ? "8px 8px" : undefined,
  };

  switch (tileId) {
    case "stripes":
      return {
        ...base,
        backgroundImage: `repeating-linear-gradient(45deg, ${patternHex} 0 4px, transparent 4px 9px)`,
      };
    case "dots":
      return {
        ...base,
        backgroundImage: `radial-gradient(${patternHex} 1.4px, transparent 1.4px)`,
      };
    case "swirl":
      return {
        ...base,
        backgroundImage: `conic-gradient(from 45deg, ${patternHex}, transparent 25%, ${patternHex} 60%, transparent)`,
      };
    case "cracks":
      return {
        ...base,
        backgroundImage: `linear-gradient(45deg, transparent 46%, ${patternHex} 48%, transparent 50%), linear-gradient(135deg, transparent 46%, ${patternHex} 48%, transparent 50%)`,
      };
    default:
      return base;
  }
}
