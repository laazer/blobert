import type { CSSProperties } from "react";

export type PatternTileDef = {
  id: string;
  label: string;
  /** Value written to ``feat_{zone}_texture_mode``. */
  textureMode: string;
};

/** Display metadata for pipeline ``texture_mode`` values (functional parity only). */
const TEXTURE_MODE_TILE_META: Record<string, { id: string; label: string }> = {
  none: { id: "plain", label: "plain" },
  spots: { id: "dots", label: "dots" },
  stripes: { id: "stripes", label: "stripes" },
  checkerboard: { id: "checkerboard", label: "checker" },
  assets: { id: "assets", label: "assets" },
};

/** Build pattern shape tiles from the active enemy's ``feat_{zone}_texture_mode`` options. */
export function buildStudioPatternTiles(textureModeOptions: readonly string[]): PatternTileDef[] {
  const out: PatternTileDef[] = [];
  for (const mode of textureModeOptions) {
    const meta = TEXTURE_MODE_TILE_META[mode];
    if (meta) {
      out.push({ id: meta.id, label: meta.label, textureMode: mode });
    }
  }
  return out;
}

export function textureModeFromTileId(
  tileId: string,
  tiles: readonly PatternTileDef[],
): string {
  return tiles.find((t) => t.id === tileId)?.textureMode ?? "none";
}

export function tileIdFromTextureMode(
  textureMode: string,
  tiles: readonly PatternTileDef[],
): string {
  return tiles.find((t) => t.textureMode === textureMode)?.id ?? "plain";
}

/** v2 Look tab: pattern shape tiles use element hue for preview. */
export function patternTileHuePreviewStyle(textureMode: string, elementHue: string): CSSProperties {
  const preview = "#0a0a10";
  switch (textureMode) {
    case "stripes":
      return {
        flex: 1,
        backgroundColor: preview,
        backgroundImage: `repeating-linear-gradient(45deg, ${elementHue} 0 3px, transparent 3px 7px)`,
      };
    case "spots":
      return {
        flex: 1,
        backgroundColor: preview,
        backgroundImage: `radial-gradient(${elementHue} 1.4px, transparent 1.4px)`,
        backgroundSize: "8px 8px",
      };
    case "checkerboard":
      return {
        flex: 1,
        backgroundColor: preview,
        backgroundImage: `linear-gradient(45deg, ${elementHue} 25%, transparent 25%, transparent 75%, ${elementHue} 75%), linear-gradient(45deg, ${elementHue} 25%, transparent 25%, transparent 75%, ${elementHue} 75%)`,
        backgroundSize: "8px 8px",
        backgroundPosition: "0 0, 4px 4px",
      };
    case "assets":
      return {
        flex: 1,
        backgroundColor: preview,
        backgroundImage: `repeating-linear-gradient(0deg, ${elementHue}55, ${elementHue}55 2px, transparent 2px, transparent 6px)`,
      };
    default:
      return { flex: 1, backgroundColor: preview };
  }
}
