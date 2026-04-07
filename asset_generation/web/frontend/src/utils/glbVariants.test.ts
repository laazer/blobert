import { describe, expect, it } from "vitest";
import {
  animatedExportRelativePath,
  parseAnimatedEnemyExportFilename,
  parseVariantFilename,
} from "./glbVariants";

describe("animatedExportRelativePath", () => {
  it("matches procedural animated stem", () => {
    expect(animatedExportRelativePath("slug", 0)).toBe("animated_exports/slug_animated_00.glb");
    expect(animatedExportRelativePath("spider", 2)).toBe("animated_exports/spider_animated_02.glb");
  });

  it("clamps variant index to 0–99", () => {
    expect(animatedExportRelativePath("slug", -1)).toBe("animated_exports/slug_animated_00.glb");
    expect(animatedExportRelativePath("slug", 100)).toBe("animated_exports/slug_animated_99.glb");
  });
});

describe("parseAnimatedEnemyExportFilename", () => {
  it("parses procedural animated basename", () => {
    expect(parseAnimatedEnemyExportFilename("slug_animated_00.glb")).toEqual({
      slug: "slug",
      variantIndex: 0,
    });
    expect(parseAnimatedEnemyExportFilename("spider_animated_02.glb")).toEqual({
      slug: "spider",
      variantIndex: 2,
    });
  });

  it("returns null for non-matching names", () => {
    expect(parseAnimatedEnemyExportFilename("misc.glb")).toBeNull();
  });
});

describe("parseVariantFilename", () => {
  it("parses trailing _NN for generic exports", () => {
    expect(parseVariantFilename("player_slime_blue_01.glb")).toEqual({
      base: "player_slime_blue",
      variantIndex: 1,
    });
  });

  it("returns null when pattern does not match", () => {
    expect(parseVariantFilename("misc.glb")).toBeNull();
    expect(parseVariantFilename("bad_1.glb")).toBeNull();
  });
});
