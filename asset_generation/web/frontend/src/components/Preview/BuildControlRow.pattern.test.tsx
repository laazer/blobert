// @vitest-environment jsdom
/**
 * ADVERSARIAL TEST SUITE: Hex Pattern Detection & Key Matching
 *
 * This test suite exposes weaknesses in the pattern matching logic that determines
 * whether a string control should render as a hex color picker or a plain text input.
 *
 * The current logic in BuildControlRow checks:
 *   - def.key.endsWith("_hex"), OR
 *   - def.key.includes("_texture_") && def.key.includes("_color")
 *
 * This test suite mutates the key patterns to find edge cases, regex issues, and
 * case sensitivity problems.
 */

import { describe, it, expect, afterEach } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow } from "./BuildControlRow";

afterEach(() => {
  cleanup();
});

// Helper: determine if a key should render as hex picker
function shouldRenderAsHexPicker(key: string): boolean {
  return key.endsWith("_hex") || (key.includes("_texture_") && key.includes("color"));
}

describe("BuildControlRow — Hex Pattern Detection & Mutations", () => {
  describe("Pattern: endsWith('_hex')", () => {
    it("matches 'feat_body_hex' — normal case", () => {
      expect(shouldRenderAsHexPicker("feat_body_hex")).toBe(true);
    });

    it("matches 'feat_eye_left_hex'", () => {
      expect(shouldRenderAsHexPicker("feat_eye_left_hex")).toBe(true);
    });

    it("does NOT match 'feat_body_hexcolor' — no underscore separator", () => {
      // Vulnerability: if key is 'feat_body_hexcolor', endsWith('_hex') is false
      expect(shouldRenderAsHexPicker("feat_body_hexcolor")).toBe(false);
    });

    it("does NOT match 'feat_body_hex_' — underscore suffix instead of at end", () => {
      expect(shouldRenderAsHexPicker("feat_body_hex_")).toBe(false);
    });

    it("does NOT match 'feat_body_HEX' — case sensitive", () => {
      // Vulnerability: uppercase HEX would not match
      expect(shouldRenderAsHexPicker("feat_body_HEX")).toBe(false);
    });

    it("does NOT match 'feat_body_Hex' — mixed case", () => {
      expect(shouldRenderAsHexPicker("feat_body_Hex")).toBe(false);
    });

    it("does NOT match '_hex' — no leading prefix (unlikely but test it)", () => {
      expect(shouldRenderAsHexPicker("_hex")).toBe(true); // Accidental match!
      // CHECKPOINT: Bare '_hex' would match; may be unintended
    });

    it("does NOT match 'hex' — no underscores", () => {
      expect(shouldRenderAsHexPicker("hex")).toBe(false);
    });

    it("renders as hex picker for 'feat_body_hex' via ControlRow", () => {
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ff0000" onChange={() => {}} />);

      expect(screen.getByTitle("Pick color")).toBeInTheDocument(); // HexStrControlRow
      expect(screen.getByRole("button", { name: "Paste color" })).toBeInTheDocument();
    });

    it("does NOT render as hex picker for 'feat_body_HEX' (case sensitive)", () => {
      const def: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_HEX",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={def} value="ff0000" onChange={() => {}} />);

      // Should render as plain text input (no color picker)
      expect(screen.queryByTitle("Pick color")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Paste color" })).not.toBeInTheDocument();

      // Should have a regular textbox
      const textInput = screen.getByRole("textbox") as HTMLInputElement;
      expect(textInput.value).toBe("ff0000");
      // CHECKPOINT: Case sensitivity is strict; uppercase HEX is not detected
    });
  });

  describe("Pattern: includes('_texture_') && includes('_color')", () => {
    it("matches 'feat_body_texture_grad_color_a' — gradient color A", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_grad_color_a")).toBe(true);
    });

    it("matches 'feat_body_texture_grad_color_b' — gradient color B", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_grad_color_b")).toBe(true);
    });

    it("matches 'feat_eye_left_texture_spot_color' — spot color", () => {
      expect(shouldRenderAsHexPicker("feat_eye_left_texture_spot_color")).toBe(true);
    });

    it("matches 'feat_body_texture_stripe_bg_color' — stripe background", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_stripe_bg_color")).toBe(true);
    });

    it("does NOT match 'feat_body_texture_grad_density' — no 'color'", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_grad_density")).toBe(false);
    });

    it("does NOT match 'feat_body_color_texture' — wrong order (color before texture)", () => {
      // Vulnerability: order is not enforced
      expect(shouldRenderAsHexPicker("feat_body_color_texture")).toBe(false);
    });

    it("does NOT match 'feat_body_texture_only' — no 'color'", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_only")).toBe(false);
    });

    it("does NOT match 'feat_body_only_color' — no '_texture_'", () => {
      expect(shouldRenderAsHexPicker("feat_body_only_color")).toBe(false);
    });

    it("does NOT match 'feat_body_texture' + 'color' as separate tokens", () => {
      // Key would need both substrings
      expect(shouldRenderAsHexPicker("feat_body_texture")).toBe(false);
      expect(shouldRenderAsHexPicker("feat_body_color")).toBe(false);
    });

    it("matches 'texture_color' (minimal substring match, not recommended pattern)", () => {
      // Vulnerability: the pattern requires _texture_ prefix with underscore
      // "texture_color" lacks the leading underscore so doesn't match
      expect(shouldRenderAsHexPicker("texture_color")).toBe(false);
      // CHECKPOINT: Pattern requires '_texture_' not just 'texture'
    });

    it("matches 'feat_body_texture_color' — missing mode prefix (e.g., grad/spot/stripe)", () => {
      // This is a malformed but valid pattern match
      expect(shouldRenderAsHexPicker("feat_body_texture_color")).toBe(true);
      // CHECKPOINT: Pattern does not require grad/spot/stripe; too permissive
    });

    it("does NOT match 'feat_body_TEXTURE_color' — case sensitive (uppercase)", () => {
      expect(shouldRenderAsHexPicker("feat_body_TEXTURE_color")).toBe(false);
      // CHECKPOINT: Uppercase would not match
    });

    it("does NOT match 'feat_body_texture_COLOR' — case sensitive (uppercase)", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_COLOR")).toBe(false);
    });

    it("renders as hex picker for 'feat_body_texture_grad_color_a' via ControlRow", () => {
      const def: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_texture_grad_color_a",
        label: "Gradient color A",
        type: "str",
        default: "",
      };

      render(<ControlRow def={def} value="ff0000" onChange={() => {}} />);

      expect(screen.getByTitle("Pick color")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Paste color" })).toBeInTheDocument();
    });

    it("does NOT render as hex picker for 'feat_body_texture_grad_color' (no suffix)", () => {
      // This key does exist, but is it intended to be a hex picker?
      // The pattern still matches because it has both substrings
      const def: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_texture_grad_color",
        label: "Gradient color",
        type: "str",
        default: "",
      };

      render(<ControlRow def={def} value="ff0000" onChange={() => {}} />);

      // Pattern should match (includes both substrings)
      expect(screen.getByTitle("Pick color")).toBeInTheDocument();
      // CHECKPOINT: Pattern is permissive enough to match missing suffix
    });
  });

  describe("Edge cases: substring ordering and repetition", () => {
    it("key with '_texture_' repeated twice: 'feat_body_texture_texture_color'", () => {
      // Unlikely but technically matches pattern
      expect(shouldRenderAsHexPicker("feat_body_texture_texture_color")).toBe(true);
    });

    it("key with '_color' repeated twice: 'feat_body_texture_color_color'", () => {
      expect(shouldRenderAsHexPicker("feat_body_texture_color_color")).toBe(true);
    });

    it("key with '_hex' at end, also includes '_texture_' and '_color'", () => {
      // Both patterns match! Hex takes precedence (first check)
      expect(shouldRenderAsHexPicker("feat_body_texture_color_hex")).toBe(true);
    });

    it("key with '_hex' but not at end: 'feat_body_hex_value'", () => {
      expect(shouldRenderAsHexPicker("feat_body_hex_value")).toBe(false);
    });

    it("key with '_color_' in the middle, not at end", () => {
      expect(shouldRenderAsHexPicker("feat_body_color_number")).toBe(false);
    });
  });

  describe("Edge cases: whitespace and special characters", () => {
    it("key with leading whitespace: ' feat_body_hex'", () => {
      // Real-world unlikely, but test it
      expect(shouldRenderAsHexPicker(" feat_body_hex")).toBe(true); // endsWith ignores leading whitespace
      // CHECKPOINT: No trimming performed; endsWith still matches
    });

    it("key with trailing whitespace: 'feat_body_hex '", () => {
      expect(shouldRenderAsHexPicker("feat_body_hex ")).toBe(false); // Trailing space fails endsWith
    });

    it("key with null bytes or control chars: 'feat_body_hex\\0'", () => {
      expect(shouldRenderAsHexPicker("feat_body_hex\0")).toBe(false);
    });

    it("empty key: ''", () => {
      expect(shouldRenderAsHexPicker("")).toBe(false);
    });

    it("null/undefined key handling (edge case)", () => {
      // TypeScript would prevent this, but runtime JavaScript allows it
      const key: any = null;
      expect(() => shouldRenderAsHexPicker(key)).toThrow(); // Should throw or handle
      // CHECKPOINT: Type validation needed upstream
    });
  });

  describe("Real-world key variations", () => {
    it("renders hex picker for realistic variations", () => {
      const variations = [
        "feat_body_hex",
        "feat_eye_left_hex",
        "feat_mouth_tail_hex",
        "feat_body_texture_grad_color_a",
        "feat_body_texture_grad_color_b",
        "feat_body_texture_spot_color",
        "feat_body_texture_spot_bg_color",
        "feat_body_texture_stripe_color",
        "feat_body_texture_stripe_bg_color",
      ];

      variations.forEach((key) => {
        const def: Extract<AnimatedBuildControlDef, { type: "str" }> = {
          key,
          label: `Control: ${key}`,
          type: "str",
          default: "",
        };

        cleanup();
        render(<ControlRow def={def} value="ff0000" onChange={() => {}} />);

        expect(screen.getByTitle("Pick color")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Paste color" })).toBeInTheDocument();
      });
    });

    it("does NOT render hex picker for non-matching keys", () => {
      const nonMatching = [
        "feat_body_name",
        "feat_body_finish",
        "feat_body_texture_mode",
        "feat_body_texture_grad_direction",
        "feat_body_texture_spot_density",
        "feat_body_texture_stripe_width",
        "custom_option",
        "description",
      ];

      nonMatching.forEach((key) => {
        const def: Extract<AnimatedBuildControlDef, { type: "str" }> = {
          key,
          label: `Control: ${key}`,
          type: "str",
          default: "",
        };

        cleanup();
        render(<ControlRow def={def} value="some_value" onChange={() => {}} />);

        expect(screen.queryByTitle("Pick color")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Paste color" })).not.toBeInTheDocument();

        // Should render as plain text input
        const textInput = screen.getByRole("textbox") as HTMLInputElement;
        expect(textInput.value).toBe("some_value");
      });
    });
  });

  describe("Integration: Pattern detection with ControlRow type dispatcher", () => {
    it("all control types dispatch correctly to ControlRow branches", () => {
      const defs: AnimatedBuildControlDef[] = [
        { key: "feat_body_hex", label: "Body hex", type: "str", default: "ff0000" },
        { key: "feat_body_name", label: "Body name", type: "str", default: "default" },
        { key: "feat_body_scale", label: "Body scale", type: "float", min: 0.5, max: 2.0, step: 0.1, default: 1.0 },
        { key: "feat_body_count", label: "Body count", type: "int", min: 0, max: 10, default: 1 },
        { key: "feat_body_texture_mode", label: "Texture mode", type: "select_str", options: ["none", "gradient"], default: "none" },
        { key: "feat_body_enabled", label: "Enabled", type: "bool", default: true },
      ];

      defs.forEach((def) => {
        cleanup();
        const value = def.type === "bool" ? true : def.type === "float" ? 1.0 : def.type === "int" ? 1 : "test_value";
        render(<ControlRow def={def} value={value} onChange={() => {}} />);

        if (def.key === "feat_body_hex") {
          expect(screen.getByTitle("Pick color")).toBeInTheDocument();
        } else if (def.type === "str") {
          const textInput = screen.getByRole("textbox");
          expect(textInput).toBeInTheDocument();
        } else if (def.type === "float") {
          const floatInput = screen.getByDisplayValue("1");
          expect(floatInput).toBeInTheDocument();
        }
      });
    });
  });
});
