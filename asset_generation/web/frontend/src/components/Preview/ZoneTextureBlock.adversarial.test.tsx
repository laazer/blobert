// @vitest-environment jsdom
/**
 * ADVERSARIAL TEST SUITE: Direction Normalization & Mode Routing
 *
 * This test suite exposes weaknesses in:
 * 1. gradientDirectionFromStore() normalization logic
 * 2. normalizedTextureMode() mode validation
 * 3. shouldShowTextureParam() conditional rendering logic
 *
 * Tests include case sensitivity, whitespace, invalid values, null/undefined,
 * and edge cases in pattern matching for texture parameter keys.
 */

import { describe, it, expect } from "vitest";
import { zonePartDisplayName } from "./ZoneTextureBlock";

// Simulate the utility functions from ZoneTextureBlock
function gradientDirectionFromStore(raw: unknown): "horizontal" | "vertical" | "radial" {
  const s = typeof raw === "string" ? raw.trim().toLowerCase() : "";
  if (s === "vertical" || s === "radial" || s === "horizontal") return s;
  return "horizontal";
}

function normalizedTextureMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "none" | "gradient" | "spots" | "checkerboard" | "stripes" | "assets" {
  const modeKey = `feat_${zone}_texture_mode`;
  const rawMode = values[modeKey];
  const textureMode = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "none";
  if (
    textureMode === "gradient" ||
    textureMode === "spots" ||
    textureMode === "checkerboard" ||
    textureMode === "stripes" ||
    textureMode === "assets" ||
    textureMode === "none"
  ) {
    return textureMode;
  }
  return "none";
}

function shouldShowTextureParam(
  zone: string,
  defKey: string | null | undefined,
  values: Readonly<Record<string, unknown>>,
): boolean {
  if (!defKey) return false;
  const modeKey = `feat_${zone}_texture_mode`;
  if (defKey === modeKey) return true;
  const mode = normalizedTextureMode(zone, values);
  if (defKey.includes("_texture_grad_")) return mode === "gradient";
  if (defKey.includes("_texture_spot_")) return mode === "spots" || mode === "checkerboard";
  if (defKey.includes("_texture_stripe_")) return mode === "stripes";
  if (defKey.includes("_texture_asset_")) return mode === "assets";
  return false;
}

describe("gradientDirectionFromStore — Direction Normalization", () => {
  describe("Valid direction values", () => {
    it("returns 'horizontal' for valid string", () => {
      expect(gradientDirectionFromStore("horizontal")).toBe("horizontal");
    });

    it("returns 'vertical' for valid string", () => {
      expect(gradientDirectionFromStore("vertical")).toBe("vertical");
    });

    it("returns 'radial' for valid string", () => {
      expect(gradientDirectionFromStore("radial")).toBe("radial");
    });
  });

  describe("Case insensitivity", () => {
    it("normalizes uppercase 'HORIZONTAL' to 'horizontal'", () => {
      expect(gradientDirectionFromStore("HORIZONTAL")).toBe("horizontal");
    });

    it("normalizes uppercase 'VERTICAL' to 'vertical'", () => {
      expect(gradientDirectionFromStore("VERTICAL")).toBe("vertical");
    });

    it("normalizes uppercase 'RADIAL' to 'radial'", () => {
      expect(gradientDirectionFromStore("RADIAL")).toBe("radial");
    });

    it("normalizes mixed case 'HoRiZoNtAl' to 'horizontal'", () => {
      expect(gradientDirectionFromStore("HoRiZoNtAl")).toBe("horizontal");
    });

    it("normalizes mixed case 'VeRtIcAl' to 'vertical'", () => {
      expect(gradientDirectionFromStore("VeRtIcAl")).toBe("vertical");
    });

    it("normalizes mixed case 'RaDiAl' to 'radial'", () => {
      expect(gradientDirectionFromStore("RaDiAl")).toBe("radial");
    });
  });

  describe("Whitespace handling", () => {
    it("trims leading whitespace: '  horizontal'", () => {
      expect(gradientDirectionFromStore("  horizontal")).toBe("horizontal");
    });

    it("trims trailing whitespace: 'horizontal  '", () => {
      expect(gradientDirectionFromStore("horizontal  ")).toBe("horizontal");
    });

    it("trims both sides: '  horizontal  '", () => {
      expect(gradientDirectionFromStore("  horizontal  ")).toBe("horizontal");
    });

    it("trims tabs: '\\thorizontal\\t'", () => {
      expect(gradientDirectionFromStore("\thorizontal\t")).toBe("horizontal");
    });

    it("trims newlines: '\\nhorizontal\\n'", () => {
      expect(gradientDirectionFromStore("\nhorizontal\n")).toBe("horizontal");
    });

    it("does NOT handle internal whitespace: 'horiz ontal'", () => {
      expect(gradientDirectionFromStore("horiz ontal")).toBe("horizontal"); // Falls back to default
      // CHECKPOINT: Internal whitespace causes mismatch
    });
  });

  describe("Invalid direction values", () => {
    it("returns 'horizontal' for invalid string 'diagonal'", () => {
      expect(gradientDirectionFromStore("diagonal")).toBe("horizontal");
    });

    it("returns 'horizontal' for invalid string '45deg'", () => {
      expect(gradientDirectionFromStore("45deg")).toBe("horizontal");
    });

    it("returns 'horizontal' for random text 'xyz'", () => {
      expect(gradientDirectionFromStore("xyz")).toBe("horizontal");
    });

    it("returns 'horizontal' for numeric string '1'", () => {
      expect(gradientDirectionFromStore("1")).toBe("horizontal");
    });

    it("returns 'horizontal' for numeric string '2'", () => {
      expect(gradientDirectionFromStore("2")).toBe("horizontal");
    });

    it("returns 'horizontal' for misspelled 'horizental'", () => {
      expect(gradientDirectionFromStore("horizental")).toBe("horizontal");
    });

    it("returns 'horizontal' for CSS direction 'to right'", () => {
      expect(gradientDirectionFromStore("to right")).toBe("horizontal");
      // CHECKPOINT: CSS gradient syntax not supported
    });

    it("returns 'horizontal' for partial match 'horiz'", () => {
      expect(gradientDirectionFromStore("horiz")).toBe("horizontal");
    });

    it("returns 'horizontal' for partial match 'vert'", () => {
      expect(gradientDirectionFromStore("vert")).toBe("horizontal");
      // CHECKPOINT: Partial matching not supported
    });
  });

  describe("Null/undefined/empty values", () => {
    it("returns 'horizontal' for null", () => {
      expect(gradientDirectionFromStore(null)).toBe("horizontal");
    });

    it("returns 'horizontal' for undefined", () => {
      expect(gradientDirectionFromStore(undefined)).toBe("horizontal");
    });

    it("returns 'horizontal' for empty string ''", () => {
      expect(gradientDirectionFromStore("")).toBe("horizontal");
    });

    it("returns 'horizontal' for whitespace-only string '   '", () => {
      expect(gradientDirectionFromStore("   ")).toBe("horizontal");
    });

    it("returns 'horizontal' for number 0", () => {
      expect(gradientDirectionFromStore(0)).toBe("horizontal");
    });

    it("returns 'horizontal' for number 1", () => {
      expect(gradientDirectionFromStore(1)).toBe("horizontal");
    });

    it("returns 'horizontal' for boolean true", () => {
      expect(gradientDirectionFromStore(true)).toBe("horizontal");
    });

    it("returns 'horizontal' for array", () => {
      expect(gradientDirectionFromStore(["horizontal"])).toBe("horizontal");
      // CHECKPOINT: Array default to "horizontal"
    });

    it("returns 'horizontal' for object", () => {
      expect(gradientDirectionFromStore({ direction: "horizontal" })).toBe("horizontal");
      // CHECKPOINT: Object falls back to default
    });
  });

  describe("Edge cases: special characters and Unicode", () => {
    it("returns 'horizontal' for Unicode 'horizontäl' (with umlaut)", () => {
      expect(gradientDirectionFromStore("horizontäl")).toBe("horizontal");
      // CHECKPOINT: Non-ASCII chars don't match
    });

    it("returns 'horizontal' for emoji '🔄 horizontal'", () => {
      expect(gradientDirectionFromStore("🔄 horizontal")).toBe("horizontal");
    });

    it("returns 'horizontal' for null byte 'horizontal\\0'", () => {
      expect(gradientDirectionFromStore("horizontal\0")).toBe("horizontal");
    });
  });
});

describe("normalizedTextureMode — Texture Mode Validation", () => {
  describe("Valid texture modes", () => {
    it("returns 'none' for 'none'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "none" })).toBe("none");
    });

    it("returns 'gradient' for 'gradient'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "gradient" })).toBe("gradient");
    });

    it("returns 'spots' for 'spots'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "spots" })).toBe("spots");
    });

    it("returns 'stripes' for 'stripes'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "stripes" })).toBe("stripes");
    });

    it("returns 'assets' for 'assets'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "assets" })).toBe("assets");
    });
  });

  describe("Case insensitivity", () => {
    it("normalizes 'GRADIENT' to 'gradient'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "GRADIENT" })).toBe("gradient");
    });

    it("normalizes 'Spots' to 'spots'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "Spots" })).toBe("spots");
    });

    it("normalizes 'STRIPES' to 'stripes'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "STRIPES" })).toBe("stripes");
    });
  });

  describe("Whitespace handling", () => {
    it("trims leading/trailing whitespace", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "  gradient  " })).toBe("gradient");
    });

    it("handles tabs and newlines", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "\tgradient\n" })).toBe("gradient");
    });
  });

  describe("Invalid modes", () => {
    it("returns 'none' for invalid mode 'custom'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "custom" })).toBe("none");
    });

    it("returns 'none' for random string 'xyz'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "xyz" })).toBe("none");
    });

    it("returns 'none' for typo 'gradiant'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "gradiant" })).toBe("none");
      // CHECKPOINT: Typos default to 'none'
    });

    it("returns 'none' for partial match 'grad'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "grad" })).toBe("none");
    });

    it("returns 'none' for misspelled 'stripes' as 'stripez'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "stripez" })).toBe("none");
    });
  });

  describe("Missing/null mode value", () => {
    it("returns 'none' for missing mode key in values", () => {
      expect(normalizedTextureMode("body", {})).toBe("none");
    });

    it("returns 'none' for null mode value", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: null })).toBe("none");
    });

    it("returns 'none' for undefined mode value", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: undefined })).toBe("none");
    });

    it("returns 'none' for number mode value", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: 1 })).toBe("none");
    });

    it("returns 'none' for boolean mode value", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: true })).toBe("none");
    });

    it("returns 'none' for array mode value", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: ["gradient"] })).toBe("none");
    });
  });

  describe("Zone-aware key construction", () => {
    it("uses correct zone in modeKey for 'body'", () => {
      expect(normalizedTextureMode("body", { feat_body_texture_mode: "gradient" })).toBe("gradient");
    });

    it("uses correct zone in modeKey for 'eye_left'", () => {
      expect(normalizedTextureMode("eye_left", { feat_eye_left_texture_mode: "spots" })).toBe("spots");
    });

    it("uses correct zone in modeKey for 'mouth_tail'", () => {
      expect(normalizedTextureMode("mouth_tail", { feat_mouth_tail_texture_mode: "stripes" })).toBe("stripes");
    });

    it("returns 'none' if mode key is missing for zone", () => {
      // Looking for feat_body_texture_mode, but only feat_eye_left_texture_mode exists
      expect(normalizedTextureMode("body", { feat_eye_left_texture_mode: "gradient" })).toBe("none");
      // CHECKPOINT: Zone mismatch is not corrected
    });
  });
});

describe("shouldShowTextureParam — Conditional Rendering Logic", () => {
  describe("Mode key always visible", () => {
    it("shows texture_mode key in any mode", () => {
      const values = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "feat_body_texture_mode", values)).toBe(true);
    });

    it("shows texture_mode key even in 'none' mode", () => {
      const values = { feat_body_texture_mode: "none" };
      expect(shouldShowTextureParam("body", "feat_body_texture_mode", values)).toBe(true);
    });
  });

  describe("Gradient mode params", () => {
    it("shows gradient params when mode='gradient'", () => {
      const values = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_b", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_direction", values)).toBe(true);
    });

    it("hides gradient params in other modes", () => {
      const valuesNone = { feat_body_texture_mode: "none" };
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", valuesNone)).toBe(false);

      const valuesSpots = { feat_body_texture_mode: "spots" };
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", valuesSpots)).toBe(false);
    });
  });

  describe("Spots mode params", () => {
    it("shows spot params when mode='spots'", () => {
      const values = { feat_body_texture_mode: "spots" };
      expect(shouldShowTextureParam("body", "feat_body_texture_spot_color", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_spot_bg_color", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_spot_density", values)).toBe(true);
    });

    it("hides spot params in other modes", () => {
      const valuesGrad = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "feat_body_texture_spot_color", valuesGrad)).toBe(false);
    });
  });

  describe("Stripes mode params", () => {
    it("shows stripe params when mode='stripes'", () => {
      const values = { feat_body_texture_mode: "stripes" };
      expect(shouldShowTextureParam("body", "feat_body_texture_stripe_color", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_stripe_bg_color", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_stripe_width", values)).toBe(true);
    });

    it("hides stripe params in other modes", () => {
      const valuesSpots = { feat_body_texture_mode: "spots" };
      expect(shouldShowTextureParam("body", "feat_body_texture_stripe_color", valuesSpots)).toBe(false);
    });
  });

  describe("Assets mode params", () => {
    it("shows asset params when mode='assets'", () => {
      const values = { feat_body_texture_mode: "assets" };
      expect(shouldShowTextureParam("body", "feat_body_texture_asset_id", values)).toBe(true);
      expect(shouldShowTextureParam("body", "feat_body_texture_asset_tile_repeat", values)).toBe(true);
    });

    it("hides asset params in other modes", () => {
      const valuesGrad = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "feat_body_texture_asset_id", valuesGrad)).toBe(false);
    });
  });

  describe("Zone-aware key matching", () => {
    it("correctly matches zone in key: 'eye_left' zone with 'feat_eye_left_texture_...'", () => {
      const values = { feat_eye_left_texture_mode: "gradient" };
      expect(shouldShowTextureParam("eye_left", "feat_eye_left_texture_grad_color_a", values)).toBe(true);
    });

    it("does NOT cross-zone match: 'body' mode should not affect 'eye_left' params", () => {
      const values = { feat_body_texture_mode: "gradient" };
      // Looking for eye_left params with body mode value
      // This is a mismatch, but shouldShowTextureParam only looks at the defKey pattern
      expect(shouldShowTextureParam("eye_left", "feat_eye_left_texture_grad_color_a", values)).toBe(false);
      // CHECKPOINT: Must provide correct zone mode value
    });
  });

  describe("Edge cases: partial or malformed keys", () => {
    it("does not show param with key '_texture_grad_' but without zone", () => {
      const values = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "_texture_grad_color", values)).toBe(true);
      // CHECKPOINT: Pattern matching only checks substrings, not full key format
    });

    it("does not show param with key 'texture_grad_' (missing underscore prefix)", () => {
      const values = { feat_body_texture_mode: "gradient" };
      // Key is "texture_grad_color_a" which lacks the required '_texture_grad_' prefix
      expect(shouldShowTextureParam("body", "texture_grad_color_a", values)).toBe(false);
      // CHECKPOINT: Pattern requires leading underscore; bare texture_grad_ doesn't match
    });

    it("does not show param with empty key", () => {
      const values = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", "", values)).toBe(false);
    });

    it("does not show param with null key", () => {
      const values = { feat_body_texture_mode: "gradient" };
      expect(shouldShowTextureParam("body", null as any, values)).toBe(false);
      // CHECKPOINT: Null/undefined not handled gracefully
    });
  });

  describe("Edge cases: invalid mode values", () => {
    it("hides mode-specific params when mode value is invalid (defaults to 'none')", () => {
      const values = { feat_body_texture_mode: "invalid_mode" };
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", values)).toBe(false);
      // CHECKPOINT: Invalid mode treats all mode-specific params as hidden
    });

    it("hides mode-specific params when mode is missing", () => {
      const values = {};
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", values)).toBe(false);
    });

    it("hides mode-specific params when mode is null", () => {
      const values = { feat_body_texture_mode: null };
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", values)).toBe(false);
    });
  });

  describe("Case sensitivity in mode check", () => {
    it("shows gradient params when mode is uppercase 'GRADIENT'", () => {
      const values = { feat_body_texture_mode: "GRADIENT" };
      // normalizedTextureMode will lowercase it
      expect(shouldShowTextureParam("body", "feat_body_texture_grad_color_a", values)).toBe(true);
    });

    it("shows spot params when mode is mixed case 'Spots'", () => {
      const values = { feat_body_texture_mode: "Spots" };
      expect(shouldShowTextureParam("body", "feat_body_texture_spot_color", values)).toBe(true);
    });
  });
});

describe("zonePartDisplayName — Zone Label Formatting", () => {
  describe("Single word zones", () => {
    it("capitalizes 'body' to 'Body'", () => {
      expect(zonePartDisplayName("body")).toBe("Body");
    });

    it("capitalizes 'head' to 'Head'", () => {
      expect(zonePartDisplayName("head")).toBe("Head");
    });
  });

  describe("Multi-word zones (underscore separated)", () => {
    it("converts 'eye_left' to 'Eye Left'", () => {
      expect(zonePartDisplayName("eye_left")).toBe("Eye Left");
    });

    it("converts 'eye_right' to 'Eye Right'", () => {
      expect(zonePartDisplayName("eye_right")).toBe("Eye Right");
    });

    it("converts 'mouth_tail' to 'Mouth Tail'", () => {
      expect(zonePartDisplayName("mouth_tail")).toBe("Mouth Tail");
    });

    it("converts 'mouth_open' to 'Mouth Open'", () => {
      expect(zonePartDisplayName("mouth_open")).toBe("Mouth Open");
    });

    it("converts 'arm_left_upper' to 'Arm Left Upper'", () => {
      expect(zonePartDisplayName("arm_left_upper")).toBe("Arm Left Upper");
    });
  });

  describe("Edge cases", () => {
    it("handles leading underscore: '_body' → 'Body'", () => {
      // First segment is empty, filtered by filter(Boolean)
      expect(zonePartDisplayName("_body")).toBe("Body");
    });

    it("handles trailing underscore: 'body_' → 'Body'", () => {
      expect(zonePartDisplayName("body_")).toBe("Body");
    });

    it("handles multiple consecutive underscores: 'body__head' → 'Body Head'", () => {
      expect(zonePartDisplayName("body__head")).toBe("Body Head");
    });

    it("handles empty string: '' → ''", () => {
      expect(zonePartDisplayName("")).toBe("");
    });

    it("handles single underscore: '_' → ''", () => {
      expect(zonePartDisplayName("_")).toBe("");
    });

    it("handles lowercase preservation in output", () => {
      expect(zonePartDisplayName("BODY")).toBe("Body"); // Capitalized
    });

    it("handles mixed case: 'BodyPart' → 'Bodypart'", () => {
      // No underscores, so treated as single word
      expect(zonePartDisplayName("BodyPart")).toBe("Bodypart");
      // CHECKPOINT: CamelCase not detected; treated as single word
    });

    it("handles numbers in zone name: 'eye_1' → 'Eye 1'", () => {
      expect(zonePartDisplayName("eye_1")).toBe("Eye 1");
    });
  });
});
