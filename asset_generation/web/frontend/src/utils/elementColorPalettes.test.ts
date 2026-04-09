// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import {
  buildFeatUpdatesFromPalette,
  DEFAULT_ELEMENT_PALETTES,
  ELEMENT_IDS,
  extractZonePaletteFromValues,
} from "./elementColorPalettes";

describe("buildFeatUpdatesFromPalette", () => {
  it("only sets keys present in defs", () => {
    const keys = new Set(["feat_body_finish", "feat_body_hex", "feat_extra_finish"]);
    const u = buildFeatUpdatesFromPalette(
      {
        body: { finish: "glossy", hex: "#abcdef" },
        head: { finish: "matte", hex: "#123456" },
      },
      keys,
    );
    expect(u).toEqual({
      feat_body_finish: "glossy",
      feat_body_hex: "#abcdef",
    });
  });

  it("sanitizes invalid finish and hex", () => {
    const keys = new Set(["feat_body_finish", "feat_body_hex"]);
    const u = buildFeatUpdatesFromPalette({ body: { finish: "nope", hex: "bad" } }, keys);
    expect(u.feat_body_finish).toBe("matte");
    expect(u.feat_body_hex).toBe("");
  });
});

describe("extractZonePaletteFromValues", () => {
  it("round-trips coarse zones", () => {
    const values = {
      feat_body_finish: "glossy",
      feat_body_hex: "#aabbcc",
      feat_head_finish: "matte",
      feat_head_hex: "#112233",
    };
    expect(extractZonePaletteFromValues(values).body).toEqual({ finish: "glossy", hex: "#aabbcc" });
  });
});

describe("DEFAULT_ELEMENT_PALETTES", () => {
  it("defines every element id with at least body zone", () => {
    for (const id of ELEMENT_IDS) {
      expect(DEFAULT_ELEMENT_PALETTES[id]?.body?.hex).toMatch(/^#[0-9a-fA-F]{6}$/);
    }
  });
});

describe("ELEMENT_IDS", () => {
  it("includes combat and environment sets", () => {
    expect(ELEMENT_IDS).toEqual([
      "physical",
      "fire",
      "ice",
      "acid",
      "poison",
      "earth",
      "forest",
      "water",
      "lightning",
    ]);
  });
});
