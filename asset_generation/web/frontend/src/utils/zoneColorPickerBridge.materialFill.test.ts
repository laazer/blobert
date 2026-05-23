import { describe, it, expect } from "vitest";
import {
  carryFillPaletteOnModeChange,
  extraZoneMaterialKeys,
  normalizedFillMode,
  partMaterialKeys,
} from "./zoneColorPickerBridge";

describe("zoneColorPickerBridge material fill", () => {
  it("extraZoneMaterialKeys maps fill_picker sub-keys", () => {
    const keys = extraZoneMaterialKeys("body");
    expect(keys.hexKey).toBe("extra_zone_body_material_hex");
    expect(keys.legacySingleKey).toBe("extra_zone_body_hex");
  });

  it("normalizedFillMode reads material_prefix_mode", () => {
    expect(
      normalizedFillMode("feat_limb_leg_0_material", {
        feat_limb_leg_0_material_mode: "gradient",
      }),
    ).toBe("gradient");
  });

  it("carryFillPaletteOnModeChange copies single hex to gradient stops", () => {
    const prefix = "extra_zone_head_material";
    const keys = partMaterialKeys(prefix, "extra_zone_head_hex");
    const carry = carryFillPaletteOnModeChange(prefix, "single", "gradient", {
      [keys.hexKey]: "aabbcc",
    });
    expect(carry[keys.colorAKey]).toBe("aabbcc");
    expect(carry[keys.colorBKey]).toBe("aabbcc");
  });
});
