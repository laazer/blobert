import { describe, it, expect } from "vitest";
import {
  buildStudioPatternTiles,
  patternTileHuePreviewStyle,
  tileIdFromTextureMode,
  textureModeFromTileId,
} from "./studioPatternPreview";

describe("buildStudioPatternTiles", () => {
  it("includes only modes present in def options (canonical synthetic)", () => {
    const tiles = buildStudioPatternTiles(["none", "spots", "stripes", "checkerboard"]);
    expect(tiles.map((t) => t.textureMode)).toEqual(["none", "spots", "stripes", "checkerboard"]);
    expect(tiles.find((t) => t.id === "swirl")).toBeUndefined();
    expect(tiles.find((t) => t.id === "cracks")).toBeUndefined();
  });

  it("maps texture mode ↔ tile id", () => {
    const tiles = buildStudioPatternTiles(["none", "stripes", "spots"]);
    expect(tileIdFromTextureMode("stripes", tiles)).toBe("stripes");
    expect(textureModeFromTileId("dots", tiles)).toBe("spots");
  });
});

describe("patternTileHuePreviewStyle", () => {
  it("uses element hue for stripe preview", () => {
    const style = patternTileHuePreviewStyle("stripes", "#ff6b3d");
    expect(String(style.backgroundImage)).toContain("#ff6b3d");
  });
});
