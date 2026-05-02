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
    const keys = new Set(["feat_body_finish", "feat_body_color_hex", "feat_extra_finish"]);
    const u = buildFeatUpdatesFromPalette(
      {
        body: { finish: "glossy", hex: "#abcdef" },
        head: { finish: "matte", hex: "#123456" },
      },
      keys,
    );
    expect(u).toEqual({
      feat_body_finish: "glossy",
      feat_body_color_hex: "#abcdef",
    });
  });

  it("sanitizes invalid finish and hex", () => {
    const keys = new Set(["feat_body_finish", "feat_body_color_hex"]);
    const u = buildFeatUpdatesFromPalette({ body: { finish: "nope", hex: "bad" } }, keys);
    expect(u.feat_body_finish).toBe("matte");
    expect(u.feat_body_color_hex).toBe("");
  });

  it("routes palette apply to gradient color fields when the zone uses gradient mode", () => {
    const keys = new Set([
      "feat_body_texture_mode",
      "feat_body_color_a",
      "feat_body_color_b",
      "feat_body_color_mode",
      "feat_body_finish",
      "feat_body_color_hex",
    ]);
    const u = buildFeatUpdatesFromPalette(
      { body: { finish: "glossy", hex: "#abcdef" } },
      keys,
      { feat_body_color_mode: "gradient" },
    );
    expect(u.feat_body_color_a).toBe("#abcdef");
    expect(typeof u.feat_body_color_b).toBe("string");
    expect(u.feat_body_color_b).not.toBe("#abcdef");
  });

  it("routes palette apply to stripes and spots fields by current zone mode", () => {
    const keys = new Set([
      "feat_body_texture_mode",
      "feat_body_texture_stripe_color",
      "feat_body_texture_stripe_bg_color",
      "feat_head_texture_mode",
      "feat_head_texture_spot_color",
      "feat_head_texture_spot_bg_color",
      "feat_head_texture_spot_color_hex",
      "feat_head_texture_spot_bg_color_hex",
      "feat_head_texture_spot_color_mode",
      "feat_head_texture_spot_bg_color_mode",
      "feat_head_texture_spot_color_image_id",
      "feat_head_texture_spot_bg_color_image_id",
      "feat_head_texture_spot_color_image_preview",
      "feat_head_texture_spot_bg_color_image_preview",
      "feat_head_texture_spot_color_image_uv_rect",
      "feat_head_texture_spot_bg_color_image_uv_rect",
      "feat_head_texture_spot_color_a",
      "feat_head_texture_spot_color_b",
      "feat_head_texture_spot_bg_color_a",
      "feat_head_texture_spot_bg_color_b",
    ]);
    const u = buildFeatUpdatesFromPalette(
      {
        body: { finish: "matte", hex: "#112233" },
        head: { finish: "gel", hex: "#445566" },
      },
      keys,
      {
        feat_body_texture_mode: "stripes",
        feat_head_texture_mode: "spots",
      },
    );
    expect(u.feat_body_texture_stripe_color).toBe("#112233");
    expect(typeof u.feat_body_texture_stripe_bg_color).toBe("string");
    expect(u.feat_body_texture_stripe_bg_color).not.toBe("#112233");
    expect(u.feat_head_texture_spot_color).toBe("#445566");
    expect(u.feat_head_texture_spot_bg_color).toBe("#78899a");
    expect(u.feat_head_texture_spot_color_hex).toBe("#445566");
    expect(u.feat_head_texture_spot_bg_color_hex).toBe("#78899a");
    expect(u.feat_head_texture_spot_color_mode).toBe("single");
    expect(u.feat_head_texture_spot_bg_color_mode).toBe("single");
    expect(u.feat_head_texture_spot_color_image_id).toBe("");
    expect(u.feat_head_texture_spot_bg_color_image_id).toBe("");
    expect(u.feat_head_texture_spot_color_image_preview).toBe("");
    expect(u.feat_head_texture_spot_bg_color_image_preview).toBe("");
    expect(u.feat_head_texture_spot_color_image_uv_rect).toBe("");
    expect(u.feat_head_texture_spot_bg_color_image_uv_rect).toBe("");
    expect(u.feat_head_texture_spot_color_a).toBe("");
    expect(u.feat_head_texture_spot_color_b).toBe("");
    expect(u.feat_head_texture_spot_bg_color_a).toBe("");
    expect(u.feat_head_texture_spot_bg_color_b).toBe("");
  });

  it("keeps spots background image mode when already configured", () => {
    const keys = new Set([
      "feat_head_texture_mode",
      "feat_head_texture_spot_color",
      "feat_head_texture_spot_color_hex",
      "feat_head_texture_spot_color_mode",
      "feat_head_texture_spot_bg_color_mode",
      "feat_head_texture_spot_bg_color_image_id",
      "feat_head_texture_spot_bg_color_image_preview",
    ]);
    const u = buildFeatUpdatesFromPalette(
      { head: { finish: "gel", hex: "#445566" } },
      keys,
      {
        feat_head_texture_mode: "spots",
        feat_head_texture_spot_bg_color_mode: "image",
        feat_head_texture_spot_bg_color_image_id: "demo_textures3",
      },
    );
    expect(u.feat_head_texture_spot_color_mode).toBe("single");
    expect(u.feat_head_texture_spot_color).toBe("#445566");
    expect(u.feat_head_texture_spot_color_hex).toBe("#445566");
    expect(u.feat_head_texture_spot_bg_color_mode).toBe("image");
    expect(u.feat_head_texture_spot_bg_color_image_id).toBeUndefined();
  });
});

describe("extractZonePaletteFromValues", () => {
  it("round-trips coarse zones", () => {
    const values = {
      feat_body_finish: "glossy",
      feat_body_color_hex: "#aabbcc",
      feat_head_finish: "matte",
      feat_head_color_hex: "#112233",
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
