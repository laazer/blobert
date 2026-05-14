// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { readPatternFillFromStore, readZoneTextureSettingsFromStore } from "./zoneTextureConverter";
import { buildFeatUpdatesFromPalette } from "./elementColorPalettes";

describe("readPatternFillFromStore", () => {
  it("reads image fill when mode is single but image_id is set", () => {
    const values = {
      feat_body_texture_background_mode: "single",
      feat_body_texture_background_hex: "",
      feat_body_texture_background_image_id: "demo_textures3",
      feat_body_texture_background_image_uv_rect: "",
    };
    const fill = readPatternFillFromStore("body", "background", values);
    expect(fill.type).toBe("image");
    if (fill.type === "image") {
      expect(fill.asset_id).toBe("demo_textures3");
    }
  });

  it("reads color fill when mode is single and image_id is empty", () => {
    const values = {
      feat_body_texture_background_mode: "single",
      feat_body_texture_background_hex: "#aabbcc",
      feat_body_texture_background_image_id: "",
    };
    const fill = readPatternFillFromStore("body", "background", values);
    expect(fill.type).toBe("color");
    if (fill.type === "color") {
      expect(fill.hex).toBe("#aabbcc");
    }
  });
});

describe("element palette + spots image background", () => {
  it("does not clear background image when background_mode is inconsistent", () => {
    const keys = new Set([
      "feat_head_texture_mode",
      "feat_head_texture_pattern_hex",
      "feat_head_texture_pattern_mode",
      "feat_head_texture_background_mode",
      "feat_head_texture_background_image_id",
    ]);
    const currentValues: Record<string, unknown> = {
      feat_head_texture_mode: "spots",
      feat_head_texture_pattern_mode: "single",
      feat_head_texture_pattern_hex: "#ff0000",
      feat_head_texture_background_mode: "single",
      feat_head_texture_background_hex: "",
      feat_head_texture_background_image_id: "demo_textures3",
    };
    const settings = readZoneTextureSettingsFromStore("head", currentValues);
    expect(settings.background.type).toBe("image");

    const u = buildFeatUpdatesFromPalette({ head: { finish: "glossy", hex: "#445566" } }, keys, currentValues);
    expect(u.feat_head_texture_background_mode).toBe("image");
    expect(u.feat_head_texture_background_image_id).toBe("demo_textures3");
    expect(u.feat_head_texture_pattern_hex).toBe("#445566");
  });
});
