import { describe, expect, it } from "vitest";
import { previewPathFromAssetsUrl } from "./previewPathFromAssetsUrl";

describe("previewPathFromAssetsUrl", () => {
  it("returns null for empty input", () => {
    expect(previewPathFromAssetsUrl(null)).toBeNull();
    expect(previewPathFromAssetsUrl("")).toBeNull();
  });

  it("extracts path from relative /api/assets URL with query", () => {
    expect(previewPathFromAssetsUrl("/api/assets/animated_exports/a.glb?t=1")).toBe("animated_exports/a.glb");
  });

  it("decodes encoded path segments", () => {
    expect(previewPathFromAssetsUrl("/api/assets/foo%2Fbar.glb")).toBe("foo/bar.glb");
  });
});
