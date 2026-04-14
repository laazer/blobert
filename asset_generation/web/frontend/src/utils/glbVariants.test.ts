import { describe, expect, it } from "vitest";
import {
  animatedExportRelativePath,
  animatedExportVersionId,
  animatedVariantIndexFromPreviewGlb,
  parseAnimatedEnemyExportFilename,
  parseVariantFilename,
  playerExportRelativePath,
  preferredAnimatedVersionIdFromPreview,
} from "./glbVariants";

describe("animatedExportVersionId", () => {
  it("matches stem used by animatedExportRelativePath", () => {
    expect(animatedExportVersionId("spider", 0)).toBe("spider_animated_00");
    expect(animatedExportVersionId("slug", 2)).toBe("slug_animated_02");
  });
});

describe("animatedExportRelativePath", () => {
  it("matches procedural animated stem", () => {
    expect(animatedExportRelativePath("slug", 0)).toBe("animated_exports/slug_animated_00.glb");
    expect(animatedExportRelativePath("spider", 2)).toBe("animated_exports/spider_animated_02.glb");
    expect(animatedExportRelativePath("spider", 2, true)).toBe(
      "animated_exports/draft/spider_animated_02.glb",
    );
  });

  it("clamps variant index to 0–99", () => {
    expect(animatedExportRelativePath("slug", -1)).toBe("animated_exports/slug_animated_00.glb");
    expect(animatedExportRelativePath("slug", 100)).toBe("animated_exports/slug_animated_99.glb");
  });
});

describe("playerExportRelativePath", () => {
  it("matches procedural player slime stem", () => {
    expect(playerExportRelativePath("blue", 0)).toBe("player_exports/player_slime_blue_00.glb");
    expect(playerExportRelativePath("Pink", 2)).toBe("player_exports/player_slime_pink_02.glb");
    expect(playerExportRelativePath("blue", 1, true)).toBe("player_exports/draft/player_slime_blue_01.glb");
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

describe("preferredAnimatedVersionIdFromPreview", () => {
  it("returns version id when preview GLB matches family", () => {
    expect(
      preferredAnimatedVersionIdFromPreview("spider", "/api/assets/animated_exports/spider_animated_02.glb"),
    ).toBe("spider_animated_02");
  });

  it("returns null when preview is another family", () => {
    expect(preferredAnimatedVersionIdFromPreview("spider", "/api/assets/animated_exports/slug_animated_01.glb")).toBeNull();
  });
});

describe("animatedVariantIndexFromPreviewGlb", () => {
  it("returns variant from preview URL when family matches", () => {
    expect(
      animatedVariantIndexFromPreviewGlb("spider", "/api/assets/animated_exports/spider_animated_01.glb?t=1"),
    ).toBe(1);
  });

  it("returns 0 when preview is another family", () => {
    expect(
      animatedVariantIndexFromPreviewGlb("spider", "/api/assets/animated_exports/slug_animated_02.glb"),
    ).toBe(0);
  });

  it("returns 0 when URL missing or not a glb path", () => {
    expect(animatedVariantIndexFromPreviewGlb("spider", null)).toBe(0);
    expect(animatedVariantIndexFromPreviewGlb(null, "/api/assets/animated_exports/spider_animated_03.glb")).toBe(0);
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
