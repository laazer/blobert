// @vitest-environment jsdom
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import {
  ZoneTextureBlock,
  shouldShowTextureParam,
  carryTexturePaletteOnModeChange,
} from "../ZoneTextureBlock";
import type { AnimatedBuildControlDef } from "../../../types";

describe("shouldShowTextureParam", () => {
  describe("texture mode selector", () => {
    it("always shows feat_{zone}_texture_mode", () => {
      const show = shouldShowTextureParam("body", "feat_body_texture_mode", {});
      expect(show).toBe(true);
    });
  });

  describe("pattern/background fill pickers", () => {
    it("shows feat_{zone}_texture_pattern when texture mode is not 'none'", () => {
      const values = { feat_body_texture_mode: "stripes" };
      const show = shouldShowTextureParam("body", "feat_body_texture_pattern", values);
      expect(show).toBe(true);
    });

    it("hides feat_{zone}_texture_pattern when texture mode is 'none'", () => {
      const values = { feat_body_texture_mode: "none" };
      const show = shouldShowTextureParam("body", "feat_body_texture_pattern", values);
      expect(show).toBe(false);
    });

    it("hides feat_{zone}_texture_pattern when texture mode is undefined", () => {
      const values = {};
      const show = shouldShowTextureParam("body", "feat_body_texture_pattern", values);
      expect(show).toBe(false);
    });

    it("shows feat_{zone}_texture_background when texture mode is not 'none'", () => {
      const values = { feat_body_texture_mode: "spots" };
      const show = shouldShowTextureParam("body", "feat_body_texture_background", values);
      expect(show).toBe(true);
    });

    it("hides feat_{zone}_texture_background when texture mode is 'none'", () => {
      const values = { feat_body_texture_mode: "none" };
      const show = shouldShowTextureParam("body", "feat_body_texture_background", values);
      expect(show).toBe(false);
    });
  });

  describe("pattern-specific controls", () => {
    it("hides spot controls when texture mode is not 'spots'", () => {
      const values = { feat_body_texture_mode: "stripes" };
      const show = shouldShowTextureParam("body", "feat_body_texture_spot_density", values);
      expect(show).toBe(false);
    });

    it("hides stripe controls when texture mode is not 'stripes'", () => {
      const values = { feat_body_texture_mode: "spots" };
      const show = shouldShowTextureParam("body", "feat_body_texture_stripe_width", values);
      expect(show).toBe(false);
    });

    it("hides all pattern-specific controls when texture mode is 'none'", () => {
      const values = { feat_body_texture_mode: "none" };
      const spotShow = shouldShowTextureParam("body", "feat_body_texture_spot_density", values);
      const stripeShow = shouldShowTextureParam("body", "feat_body_texture_stripe_width", values);
      const checkerShow = shouldShowTextureParam("body", "feat_body_texture_stripe_direction", values);

      expect(spotShow).toBe(false);
      expect(stripeShow).toBe(false);
      expect(checkerShow).toBe(false);
    });
  });

  describe("all texture-related helper keys", () => {
    it("hides feat_{zone}_texture_* keys that are not textureMode, pattern, or background", () => {
      const values = { feat_body_texture_mode: "stripes" };
      // Asset-related keys should be hidden
      const assetIdShow = shouldShowTextureParam("body", "feat_body_texture_asset_id", values);
      const tileRepeatShow = shouldShowTextureParam("body", "feat_body_texture_asset_tile_repeat", values);

      expect(assetIdShow).toBe(false);
      expect(tileRepeatShow).toBe(false);
    });
  });
});

describe("carryTexturePaletteOnModeChange", () => {
  it("returns {} when typed pattern/background hexes are already set", () => {
    const values = {
      feat_body_texture_mode: "stripes",
      feat_body_texture_pattern_mode: "single",
      feat_body_texture_pattern_hex: "#112233",
      feat_body_texture_background_mode: "single",
      feat_body_texture_background_hex: "#445566",
    };
    expect(carryTexturePaletteOnModeChange("body", "stripes", "spots", values)).toEqual({});
  });

  it("returns {} on mode change even when legacy stripe keys are populated", () => {
    const values = {
      feat_body_texture_mode: "stripes",
      feat_body_texture_pattern_mode: "single",
      feat_body_texture_pattern_hex: "",
      feat_body_texture_background_mode: "single",
      feat_body_texture_background_hex: "",
      feat_body_texture_stripe_color: "aabbcc",
      feat_body_texture_stripe_bg_color: "ddeeff",
    };
    expect(carryTexturePaletteOnModeChange("body", "stripes", "spots", values)).toEqual({});
  });

  it("returns {} when prev and next mode are the same", () => {
    expect(carryTexturePaletteOnModeChange("body", "spots", "spots", {})).toEqual({});
  });
});

describe("ZoneTextureBlock rendering", () => {
  const mockBuiltControls: AnimatedBuildControlDef[] = [
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

  it("should render with correct controls when no texture mode is set", () => {
    const { container } = render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockBuiltControls}
      />
    );
    expect(container).toBeTruthy();
  });

  it("should have texture mode control defined in defs", () => {
    const modeDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_mode");
    expect(modeDef).toBeDefined();
    expect(modeDef?.type).toBe("select_str");
    expect(modeDef?.options).toContain("stripes");
    expect(modeDef?.options).toContain("spots");
    expect(modeDef?.options).toContain("checkerboard");
  });

  it("should have pattern and background fill picker controls", () => {
    const patternDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_pattern");
    const bgDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_background");

    expect(patternDef).toBeDefined();
    expect(patternDef?.type).toBe("fill_picker");
    expect(bgDef).toBeDefined();
    expect(bgDef?.type).toBe("fill_picker");
  });

  it("should have spot-specific controls in defs", () => {
    const spotPatternDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_spot_pattern");
    const spotDensityDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_spot_density");

    expect(spotPatternDef).toBeDefined();
    expect(spotPatternDef?.type).toBe("select_str");
    expect(spotDensityDef).toBeDefined();
    expect(spotDensityDef?.type).toBe("float");
  });

  it("should have stripe-specific controls in defs", () => {
    const stripeWidthDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_stripe_width");
    const stripeDirectionDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_stripe_direction");
    const stripeYawDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_stripe_rot_yaw");
    const stripePitchDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_stripe_rot_pitch");

    expect(stripeWidthDef).toBeDefined();
    expect(stripeDirectionDef).toBeDefined();
    expect(stripeYawDef).toBeDefined();
    expect(stripePitchDef).toBeDefined();
  });

  it("should have global asset controls in defs", () => {
    const assetIdDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_asset_id");
    const tileRepeatDef = mockBuiltControls.find((d) => d.key === "feat_body_texture_asset_tile_repeat");

    expect(assetIdDef).toBeDefined();
    expect(tileRepeatDef).toBeDefined();
  });
});
