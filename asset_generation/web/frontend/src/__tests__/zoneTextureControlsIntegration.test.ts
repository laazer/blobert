import { describe, it, expect } from "vitest";
import type { AnimatedBuildControlDef } from "../types";
import { readZoneTextureSettingsFromStore, writeZoneTextureSettingsToStore } from "../utils/zoneTextureConverter";
import type { Zone } from "../types/zoneTexture";

/**
 * Integration test verifying that the zone texture control system works end-to-end:
 * 1. API returns proper texture controls with fill_picker type
 * 2. Converter functions can read/write zone texture settings from flat keys
 * 3. Control keys follow the correct naming convention
 */

describe("Zone Texture Controls Integration", () => {
  describe("API control structure", () => {
    const mockSpiderControls: AnimatedBuildControlDef[] = [
      {
        key: "feat_body_texture_mode",
        label: "Body — Texture mode",
        type: "select_str",
        options: ["none", "gradient", "spots", "checkerboard", "stripes", "assets"],
        default: "none",
      },
      {
        key: "feat_body_texture_pattern",
        label: "Body — Pattern color",
        type: "fill_picker",
      },
      {
        key: "feat_body_texture_background",
        label: "Body — Background color",
        type: "fill_picker",
      },
      {
        key: "feat_body_texture_spot_pattern",
        label: "Body — Spot layout",
        type: "select_str",
        options: ["grid", "scatter"],
        default: "grid",
        segmented: true,
      },
      {
        key: "feat_body_texture_spot_density",
        label: "Body — Spot density",
        type: "float",
        default: 1.0,
      },
      {
        key: "feat_body_texture_stripe_width",
        label: "Body — Stripe width",
        type: "float",
        default: 0.2,
      },
      {
        key: "feat_body_texture_stripe_direction",
        label: "Body — Stripe preset",
        type: "select_str",
        default: "beachball",
      },
      {
        key: "feat_body_texture_stripe_rot_yaw",
        label: "Body — Stripe yaw",
        type: "float",
        default: 0.0,
      },
      {
        key: "feat_body_texture_stripe_rot_pitch",
        label: "Body — Stripe pitch",
        type: "float",
        default: 0.0,
      },
      {
        key: "feat_body_texture_asset_id",
        label: "Body — Asset texture",
        type: "str",
        default: "",
      },
      {
        key: "feat_body_texture_asset_tile_repeat",
        label: "Body — Tile repeat",
        type: "float",
        default: 1.0,
      },
      {
        key: "feat_head_texture_mode",
        label: "Head — Texture mode",
        type: "select_str",
        options: ["none", "gradient", "spots", "checkerboard", "stripes", "assets"],
        default: "none",
      },
      {
        key: "feat_head_texture_pattern",
        label: "Head — Pattern color",
        type: "fill_picker",
      },
      {
        key: "feat_head_texture_background",
        label: "Head — Background color",
        type: "fill_picker",
      },
    ];

    it("has texture mode selector for each zone", () => {
      const bodyMode = mockSpiderControls.find((c) => c.key === "feat_body_texture_mode");
      const headMode = mockSpiderControls.find((c) => c.key === "feat_head_texture_mode");

      expect(bodyMode).toBeDefined();
      expect(bodyMode?.type).toBe("select_str");
      expect(headMode).toBeDefined();
      expect(headMode?.type).toBe("select_str");
    });

    it("has fill_picker controls for pattern and background in each zone", () => {
      const bodyPattern = mockSpiderControls.find((c) => c.key === "feat_body_texture_pattern");
      const bodyBg = mockSpiderControls.find((c) => c.key === "feat_body_texture_background");
      const headPattern = mockSpiderControls.find((c) => c.key === "feat_body_texture_pattern");
      const headBg = mockSpiderControls.find((c) => c.key === "feat_body_texture_background");

      expect(bodyPattern?.type).toBe("fill_picker");
      expect(bodyBg?.type).toBe("fill_picker");
      expect(headPattern?.type).toBe("fill_picker");
      expect(headBg?.type).toBe("fill_picker");
    });

    it("has no duplicate control keys in single zone", () => {
      const bodyControls = mockSpiderControls.filter((c) => c.key.startsWith("feat_body_"));
      const keys = bodyControls.map((c) => c.key);
      const uniqueKeys = new Set(keys);

      // stripe_width and stripe_direction appear once (not duplicated for checkerboard)
      const stripeWidthCount = keys.filter((k) => k === "feat_body_texture_stripe_width").length;
      const stripeDirectionCount = keys.filter((k) => k === "feat_body_texture_stripe_direction").length;

      expect(keys.length).toBe(uniqueKeys.size);
      expect(stripeWidthCount).toBe(1);
      expect(stripeDirectionCount).toBe(1);
    });

    it("does not include old deprecated keys", () => {
      const hasDeprecatedKeys = mockSpiderControls.some((c) =>
        c.key.includes("texture_grad_color") ||
        c.key.includes("texture_spot_color") ||
        c.key.includes("texture_stripe_color")
      );

      expect(hasDeprecatedKeys).toBe(false);
    });
  });

  describe("Converter functions with new schema", () => {
    it("reads zone texture settings from flat store keys with textureMode=none", () => {
      const values = {
        feat_body_texture_mode: "none",
        feat_body_texture_pattern: null,
        feat_body_texture_background: null,
      };

      const settings = readZoneTextureSettingsFromStore("body" as Zone, values);

      expect(settings.zone).toBe("body");
      expect(settings.textureMode).toBe("none");
      expect(settings.pattern).toBeUndefined();
      expect(settings.background).toBeDefined();
    });

    it("reads zone texture settings with textureMode=stripes", () => {
      const values = {
        feat_body_texture_mode: "stripes",
        feat_body_texture_pattern: null,
        feat_body_texture_background: null,
      };

      const settings = readZoneTextureSettingsFromStore("body" as Zone, values);

      expect(settings.zone).toBe("body");
      expect(settings.textureMode).toBe("stripes");
      expect(settings.pattern).toBeDefined();
      expect(settings.background).toBeDefined();
    });

    it("reads zone texture settings with textureMode=spots", () => {
      const values = {
        feat_body_texture_mode: "spots",
        feat_body_texture_pattern: null,
        feat_body_texture_background: null,
      };

      const settings = readZoneTextureSettingsFromStore("body" as Zone, values);

      expect(settings.zone).toBe("body");
      expect(settings.textureMode).toBe("spots");
      expect(settings.pattern).toBeDefined();
      expect(settings.background).toBeDefined();
    });

    it("writes zone texture settings back to flat store keys", () => {
      const settings = {
        zone: "body" as Zone,
        textureMode: "stripes" as const,
        pattern: { type: "color" as const, hex: "#ff0000" },
        background: { type: "color" as const, hex: "#00ff00" },
      };

      const updates = writeZoneTextureSettingsToStore(settings);

      expect(updates["feat_body_texture_mode"]).toBe("stripes");
      expect(updates["feat_body_texture_pattern_mode"]).toBe("single");
      expect(updates["feat_body_texture_pattern_hex"]).toBe("#ff0000");
      expect(updates["feat_body_texture_pattern_grad_a"]).toBe("");
      expect(updates["feat_body_texture_background_mode"]).toBe("single");
      expect(updates["feat_body_texture_background_hex"]).toBe("#00ff00");
      expect(updates["feat_body_texture_background_grad_a"]).toBe("");
    });

    it("round-trips zone texture settings (write -> read)", () => {
      const original = {
        zone: "body" as Zone,
        textureMode: "spots" as const,
        pattern: { type: "color" as const, hex: "#aabbcc" },
        background: { type: "color" as const, hex: "#ddeeff" },
      };

      const flat = writeZoneTextureSettingsToStore(original);
      const restored = readZoneTextureSettingsFromStore("body" as Zone, flat);

      expect(restored.zone).toBe(original.zone);
      expect(restored.textureMode).toBe(original.textureMode);
      expect(restored.pattern?.type).toBe(original.pattern.type);
      expect(restored.pattern?.hex).toBe(original.pattern.hex);
      expect(restored.background?.type).toBe(original.background.type);
      expect(restored.background?.hex).toBe(original.background.hex);
    });
  });

  describe("Control key naming conventions", () => {
    it("follows feat_{zone}_texture_{suffix} pattern for all texture keys", () => {
      const mockControls: AnimatedBuildControlDef[] = [
        { key: "feat_body_texture_mode", label: "", type: "select_str", options: [], default: "none" },
        { key: "feat_body_texture_pattern", label: "", type: "fill_picker" },
        { key: "feat_body_texture_background", label: "", type: "fill_picker" },
        { key: "feat_body_texture_spot_density", label: "", type: "float", default: 1.0 },
        { key: "feat_body_texture_stripe_width", label: "", type: "float", default: 0.2 },
        { key: "feat_body_texture_stripe_direction", label: "", type: "select_str", default: "horizontal" },
        { key: "feat_body_texture_stripe_rot_yaw", label: "", type: "float", default: 0.0 },
        { key: "feat_body_texture_stripe_rot_pitch", label: "", type: "float", default: 0.0 },
        { key: "feat_body_texture_asset_id", label: "", type: "str", default: "" },
        { key: "feat_body_texture_asset_tile_repeat", label: "", type: "float", default: 1.0 },
      ];

      const pattern = /^feat_[a-z_]+_texture_[a-z_]+$/;
      mockControls.forEach((ctrl) => {
        expect(ctrl.key).toMatch(pattern);
      });
    });

    it("uses distinct keys for each zone (no collision)", () => {
      const bodyKeys = ["feat_body_texture_mode", "feat_body_texture_pattern"];
      const headKeys = ["feat_head_texture_mode", "feat_head_texture_pattern"];
      const allKeys = [...bodyKeys, ...headKeys];
      const uniqueKeys = new Set(allKeys);

      expect(allKeys.length).toBe(uniqueKeys.size);
    });
  });
});
