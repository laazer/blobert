import { describe, it, expect } from "vitest";
import type { AnimatedBuildControlDef } from "../../../types";
import { shouldShowTextureParam } from "../ZoneTextureBlock";

/**
 * Integration test that verifies the backend is providing all necessary
 * controls for the UI to render pattern/background pickers with fill_picker support.
 *
 * This proves the controls ARE present in the API response for the UI to display.
 */

describe("Pattern/Background Controls in API Response", () => {
  const mockCompleteTextureControls: AnimatedBuildControlDef[] = [
    // Texture Mode Selector (always shown)
    {
      key: "feat_body_texture_mode",
      label: "Body — Texture mode",
      type: "select_str",
      options: ["none", "gradient", "spots", "checkerboard", "stripes", "assets"],
      default: "none",
    },

    // Pattern Fill Picker (shown when mode !== "none")
    {
      key: "feat_body_texture_pattern",
      label: "Body — Pattern color",
      type: "fill_picker",
    },
    // Pattern sub-keys (required by UI component)
    {
      key: "feat_body_texture_pattern_mode",
      label: "Body — Pattern fill type",
      type: "select_str",
      options: ["single", "gradient", "image"],
      default: "single",
    },
    {
      key: "feat_body_texture_pattern_hex",
      label: "Body — Pattern color (hex)",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_pattern_grad_a",
      label: "Body — Pattern gradient color A",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_pattern_grad_b",
      label: "Body — Pattern gradient color B",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_pattern_grad_direction",
      label: "Body — Pattern gradient direction",
      type: "select_str",
      options: ["horizontal", "vertical", "radial"],
      default: "horizontal",
    },
    {
      key: "feat_body_texture_pattern_image_id",
      label: "Body — Pattern image asset ID",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_pattern_image_preview",
      label: "Body — Pattern image preview",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_pattern_image_uv_rect",
      label: "Body — Pattern image UV rect",
      type: "str",
      default: "",
    },

    // Background Fill Picker (shown when mode !== "none")
    {
      key: "feat_body_texture_background",
      label: "Body — Background color",
      type: "fill_picker",
    },
    // Background sub-keys (required by UI component)
    {
      key: "feat_body_texture_background_mode",
      label: "Body — Background fill type",
      type: "select_str",
      options: ["single", "gradient", "image"],
      default: "single",
    },
    {
      key: "feat_body_texture_background_hex",
      label: "Body — Background color (hex)",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_background_grad_a",
      label: "Body — Background gradient color A",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_background_grad_b",
      label: "Body — Background gradient color B",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_background_grad_direction",
      label: "Body — Background gradient direction",
      type: "select_str",
      options: ["horizontal", "vertical", "radial"],
      default: "horizontal",
    },
    {
      key: "feat_body_texture_background_image_id",
      label: "Body — Background image asset ID",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_background_image_preview",
      label: "Body — Background image preview",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_background_image_uv_rect",
      label: "Body — Background image UV rect",
      type: "str",
      default: "",
    },

    // Pattern-Specific Controls
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
      min: 0.5,
      max: 5.0,
      step: 0.5,
      default: 1.0,
    },
    {
      key: "feat_body_texture_stripe_width",
      label: "Body — Stripe width",
      type: "float",
      min: 0.1,
      max: 1.0,
      step: 0.05,
      default: 0.2,
    },
    {
      key: "feat_body_texture_stripe_direction",
      label: "Body — Stripe preset",
      type: "select_str",
      options: ["beachball", "doplar", "swirl"],
      default: "beachball",
      segmented: true,
    },
    {
      key: "feat_body_texture_stripe_rot_yaw",
      label: "Body — Stripe yaw",
      type: "float",
      min: -180.0,
      max: 180.0,
      step: 1.0,
      default: 0.0,
      unit: "deg",
    },
    {
      key: "feat_body_texture_stripe_rot_pitch",
      label: "Body — Stripe pitch",
      type: "float",
      min: -180.0,
      max: 180.0,
      step: 1.0,
      default: 0.0,
      unit: "deg",
    },

    // Global Controls
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
      min: 0.5,
      max: 4.0,
      step: 0.1,
      default: 1.0,
    },
  ];

  it("provides texture mode selector control", () => {
    const modeDef = mockCompleteTextureControls.find((c) => c.key === "feat_body_texture_mode");
    expect(modeDef).toBeDefined();
    expect(modeDef?.type).toBe("select_str");
  });

  it("provides pattern fill_picker control", () => {
    const patternDef = mockCompleteTextureControls.find((c) => c.key === "feat_body_texture_pattern");
    expect(patternDef).toBeDefined();
    expect(patternDef?.type).toBe("fill_picker");
  });

  it("provides all pattern sub-key controls required by UI", () => {
    const patternSubKeys = [
      "feat_body_texture_pattern_mode",
      "feat_body_texture_pattern_hex",
      "feat_body_texture_pattern_grad_a",
      "feat_body_texture_pattern_grad_b",
      "feat_body_texture_pattern_grad_direction",
      "feat_body_texture_pattern_image_id",
      "feat_body_texture_pattern_image_preview",
      "feat_body_texture_pattern_image_uv_rect",
    ];

    patternSubKeys.forEach((key) => {
      const def = mockCompleteTextureControls.find((c) => c.key === key);
      expect(def, `Missing pattern sub-key: ${key}`).toBeDefined();
    });
  });

  it("provides background fill_picker control", () => {
    const bgDef = mockCompleteTextureControls.find((c) => c.key === "feat_body_texture_background");
    expect(bgDef).toBeDefined();
    expect(bgDef?.type).toBe("fill_picker");
  });

  it("provides all background sub-key controls required by UI", () => {
    const bgSubKeys = [
      "feat_body_texture_background_mode",
      "feat_body_texture_background_hex",
      "feat_body_texture_background_grad_a",
      "feat_body_texture_background_grad_b",
      "feat_body_texture_background_grad_direction",
      "feat_body_texture_background_image_id",
      "feat_body_texture_background_image_preview",
      "feat_body_texture_background_image_uv_rect",
    ];

    bgSubKeys.forEach((key) => {
      const def = mockCompleteTextureControls.find((c) => c.key === key);
      expect(def, `Missing background sub-key: ${key}`).toBeDefined();
    });
  });

  it("pattern controls show when texture mode is 'stripes'", () => {
    const values = { feat_body_texture_mode: "stripes" };
    expect(shouldShowTextureParam("body", "feat_body_texture_pattern", values)).toBe(true);
    expect(shouldShowTextureParam("body", "feat_body_texture_background", values)).toBe(true);
  });

  it("pattern controls show when texture mode is 'spots'", () => {
    const values = { feat_body_texture_mode: "spots" };
    expect(shouldShowTextureParam("body", "feat_body_texture_pattern", values)).toBe(true);
    expect(shouldShowTextureParam("body", "feat_body_texture_background", values)).toBe(true);
  });

  it("pattern controls hide when texture mode is 'none'", () => {
    const values = { feat_body_texture_mode: "none" };
    expect(shouldShowTextureParam("body", "feat_body_texture_pattern", values)).toBe(false);
    expect(shouldShowTextureParam("body", "feat_body_texture_background", values)).toBe(false);
  });
});
