// @vitest-environment jsdom
import { afterEach, describe, expect, it } from "vitest";
import { DEFAULT_ELEMENT_PALETTES } from "./elementColorPalettes";
import {
  ELEMENT_PALETTE_OVERRIDES_LS,
  builtinElementDefaultOptions,
  clearElementPaletteOverride,
  loadElementPaletteOverrides,
  resolveElementPalette,
  setElementMaterialOverride,
  setElementPaletteOverride,
} from "./elementPaletteOverrides";
import { mergeCanonicalZoneControlsForAllSlugs } from "./animatedZoneControlsMerge";

afterEach(() => {
  localStorage.removeItem(ELEMENT_PALETTE_OVERRIDES_LS);
});

describe("elementPaletteOverrides", () => {
  it("merges overrides onto built-in palettes per zone", () => {
    setElementPaletteOverride("fire", {
      body: { finish: "matte", hex: "#111111" },
    });
    const merged = resolveElementPalette("fire");
    expect(merged.body).toEqual({ finish: "matte", hex: "#111111" });
    expect(merged.head?.hex).toBe(DEFAULT_ELEMENT_PALETTES.fire.head?.hex);
  });

  it("clears override when palette matches built-in", () => {
    setElementPaletteOverride("ice", { ...DEFAULT_ELEMENT_PALETTES.ice });
    expect(loadElementPaletteOverrides().ice).toBeUndefined();
  });

  it("reset removes stored override", () => {
    setElementPaletteOverride("poison", {
      extra: { finish: "gel", hex: "#abcdef" },
    });
    clearElementPaletteOverride("poison");
    expect(resolveElementPalette("poison").extra?.hex).toBe(
      DEFAULT_ELEMENT_PALETTES.poison.extra?.hex,
    );
  });

  it("persists full material options beyond finish and hex", () => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    const knownDefKeys = new Set((controls.spider ?? []).map((d) => d.key));
    const builtin = builtinElementDefaultOptions("fire", knownDefKeys);
    const draft = {
      ...builtin,
      feat_body_finish: "metallic",
      feat_body_texture_mode: "stripes",
    };
    setElementMaterialOverride("fire", draft, knownDefKeys);
    const stored = loadElementPaletteOverrides().fire?.options;
    expect(stored?.feat_body_texture_mode).toBe("stripes");
    expect(stored?.feat_body_finish).toBe("metallic");
  });
});
