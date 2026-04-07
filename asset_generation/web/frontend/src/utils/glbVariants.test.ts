import { describe, expect, it } from "vitest";
import type { Asset } from "../types";
import {
  parseAssetPathFromGlbUrl,
  parseVariantFilename,
  variantsInSameFamily,
} from "./glbVariants";

function asset(dir: string, name: string): Asset {
  return { dir, name, path: `${dir}/${name}`, size: 1 };
}

describe("glbVariants", () => {
  it("parses animated enemy filenames", () => {
    expect(parseVariantFilename("tar_slug_animated_00.glb")).toEqual({
      base: "tar_slug_animated",
      variantIndex: 0,
    });
    expect(parseVariantFilename("adhesion_bug_animated_02.glb")).toEqual({
      base: "adhesion_bug_animated",
      variantIndex: 2,
    });
  });

  it("parses player slime filenames", () => {
    expect(parseVariantFilename("player_slime_blue_01.glb")).toEqual({
      base: "player_slime_blue",
      variantIndex: 1,
    });
  });

  it("returns null for non-variant names", () => {
    expect(parseVariantFilename("misc.glb")).toBeNull();
    expect(parseVariantFilename("bad_1.glb")).toBeNull();
  });

  it("parses asset path from viewer URL", () => {
    expect(parseAssetPathFromGlbUrl("/api/assets/animated_exports/x_00.glb?t=1")).toBe(
      "animated_exports/x_00.glb",
    );
    expect(parseAssetPathFromGlbUrl(null)).toBeNull();
  });

  it("groups variants in same family", () => {
    const assets: Asset[] = [
      asset("animated_exports", "tar_slug_animated_00.glb"),
      asset("animated_exports", "tar_slug_animated_01.glb"),
      asset("animated_exports", "adhesion_bug_animated_00.glb"),
      asset("player_exports", "tar_slug_animated_99.glb"),
    ];
    const active = assets[0]!;
    const v = variantsInSameFamily(assets, active);
    expect(v.map((a) => a.name)).toEqual([
      "tar_slug_animated_00.glb",
      "tar_slug_animated_01.glb",
    ]);
  });
});
