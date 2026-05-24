import { describe, it, expect } from "vitest";
import {
  STUDIO_PREVIEW_SCALE_DEFAULT_INDEX,
  STUDIO_PREVIEW_SCALE_LEVELS,
  clampPreviewScaleIndex,
  studioPreviewScaleLabel,
} from "./studioPreviewScale";
import { studioPreviewViewportGlowBackground } from "../styles/studioPreviewStyles";

describe("studioPreviewScale", () => {
  it("defaults to 80% (20% smaller than full)", () => {
    expect(STUDIO_PREVIEW_SCALE_LEVELS[STUDIO_PREVIEW_SCALE_DEFAULT_INDEX]).toBe(0.8);
    expect(studioPreviewScaleLabel(0.8)).toBe("80%");
  });

  it("clamps scale index to valid range", () => {
    expect(clampPreviewScaleIndex(-1)).toBe(0);
    expect(clampPreviewScaleIndex(99)).toBe(STUDIO_PREVIEW_SCALE_LEVELS.length - 1);
    expect(clampPreviewScaleIndex(1.7)).toBe(2);
  });

  it("builds layered radial glow background for the viewport frame", () => {
    const bg = studioPreviewViewportGlowBackground("#7c8cf5");
    expect(bg).toContain("radial-gradient");
    expect(bg).toContain("#7c8cf5");
  });
});
