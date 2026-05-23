import { describe, it, expect } from "vitest";
import { patternTilePreviewStyle } from "./studioPatternPreview";

describe("patternTilePreviewStyle", () => {
  it("returns stripe gradient for stripes tile", () => {
    const style = patternTilePreviewStyle("stripes", "#e6531f", "#ffd23d");
    expect(String(style.backgroundImage)).toContain("repeating-linear-gradient");
    expect(style.backgroundColor).toBe("#e6531f");
  });

  it("returns plain body color for plain tile", () => {
    const style = patternTilePreviewStyle("plain", "#e6531f", "#ffd23d");
    expect(style.backgroundColor).toBe("#e6531f");
    expect(style.backgroundImage).toBeUndefined();
  });
});
