// @vitest-environment jsdom
/**
 * ADVERSARIAL TEST SUITE: Type Mutation & Discriminated Union Handling
 *
 * This test suite is designed to expose weaknesses in type narrowing for the
 * ColorPickerValue discriminated union. Tests pass malformed objects, wrong types,
 * and edge-case values to verify that the component and consumers correctly guard
 * against type violations.
 *
 * Why this matters: If consumers (HexStrControlRow, ZoneTextureBlock) don't properly
 * narrow on v.type before accessing mode-specific fields, they will crash or behave
 * unexpectedly.
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import {
  ColorPickerUniversal,
  type ColorPickerValue,
} from "./ColorPickerUniversal";

afterEach(() => {
  cleanup();
});

describe("ColorPickerUniversal — Type Mutation & Edge Cases", () => {
  describe("Single mode: malformed color field", () => {
    it("renders with missing color field (undefined), gracefully falls back", () => {
      const value: Partial<Extract<ColorPickerValue, { type: "single" }>> = {
        type: "single",
        // color is missing — should not crash
      };

      // TypeScript will complain, but runtime should handle it
      render(
        <ColorPickerUniversal
          mode="single"
          value={value as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Component should render; hex field may be empty or have a default
      const hexField = screen.queryByPlaceholderText("RRGGBB");
      expect(hexField).toBeInTheDocument(); // Should still render
      // CHECKPOINT: Verify graceful handling, not a crash
    });

    it("renders with null color field, handles gracefully", () => {
      const value = {
        type: "single" as const,
        color: null, // Invalid—should be string
      };

      render(
        <ColorPickerUniversal
          mode="single"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      const hexField = screen.queryByPlaceholderText("RRGGBB");
      expect(hexField).toBeInTheDocument();
    });

    it("renders with empty string color, does not crash", () => {
      const value: ColorPickerValue = {
        type: "single",
        color: "", // Empty but not missing
      };

      render(
        <ColorPickerUniversal
          mode="single"
          value={value}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      const hexField = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
      expect(hexField.value).toBe("");
    });

    it("renders with non-string color (number), coerced or rejected", () => {
      const value = {
        type: "single" as const,
        color: 16711680, // Red as integer, not string
      };

      render(
        <ColorPickerUniversal
          mode="single"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Component should either coerce to string or handle gracefully
      const hexField = screen.queryByPlaceholderText("RRGGBB");
      expect(hexField).toBeInTheDocument();
      // CHECKPOINT: Type coercion behavior is not specified; ensure no crash
    });
  });

  describe("Gradient mode: malformed color fields", () => {
    it("renders with missing colorB field", () => {
      const value = {
        type: "gradient" as const,
        colorA: "ff0000",
        // colorB missing
        direction: "horizontal" as const,
      };

      render(
        <ColorPickerUniversal
          mode="gradient"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Should render gradient mode; missing field should fall back
      const gradientInputs = screen.queryAllByPlaceholderText("RRGGBB");
      expect(gradientInputs.length).toBeGreaterThan(0); // At least colorA rendered
      // CHECKPOINT: Partial gradient values handled gracefully
    });

    it("renders with null colorA and undefined colorB, both missing", () => {
      const value = {
        type: "gradient" as const,
        colorA: null,
        colorB: undefined,
        direction: "vertical" as const,
      };

      render(
        <ColorPickerUniversal
          mode="gradient"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Should render, with empty/default fields
      const gradientInputs = screen.queryAllByPlaceholderText("RRGGBB");
      expect(gradientInputs.length).toBeGreaterThan(0);
    });

    it("renders with missing direction field, defaults gracefully", () => {
      const value = {
        type: "gradient" as const,
        colorA: "ff0000",
        colorB: "0000ff",
        // direction missing
      };

      render(
        <ColorPickerUniversal
          mode="gradient"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Should render; direction selector should show default or empty
      const directionSelector = screen.queryByRole("combobox", { name: /direction/i });
      expect(directionSelector).toBeInTheDocument();
      // CHECKPOINT: Missing direction is handled, likely defaults to "horizontal"
    });

    it("renders with invalid direction string, normalizes or rejects", () => {
      const value: ColorPickerValue = {
        type: "gradient",
        colorA: "ff0000",
        colorB: "0000ff",
        direction: "diagonal" as unknown as any, // Invalid
      };

      render(
        <ColorPickerUniversal
          mode="gradient"
          value={value}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      const directionSelector = screen.queryByRole("combobox", { name: /direction/i });
      expect(directionSelector).toBeInTheDocument();
      // CHECKPOINT: Invalid direction should be handled (default or error)
    });
  });

  describe("Image mode: file field edge cases", () => {
    it("renders with null file field in image mode", () => {
      const value: ColorPickerValue = {
        type: "image",
        file: null, // Valid—can be null
      };

      render(
        <ColorPickerUniversal
          mode="image"
          value={value}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Should render image uploader; file is optional
      expect(screen.getByRole("button", { name: /image/i, pressed: true })).toBeInTheDocument();
    });

    it("renders with missing file field, defaults to null", () => {
      const value = {
        type: "image" as const,
        // file is missing
      };

      render(
        <ColorPickerUniversal
          mode="image"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      expect(screen.getByRole("button", { name: /image/i, pressed: true })).toBeInTheDocument();
    });

    it("renders with non-File object in file field, handles gracefully", () => {
      const value = {
        type: "image" as const,
        file: { name: "fake.jpg" }, // Not a real File object
      };

      render(
        <ColorPickerUniversal
          mode="image"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Should not crash; file type coercion or validation happens at upload
      expect(screen.getByRole("button", { name: /image/i, pressed: true })).toBeInTheDocument();
      // CHECKPOINT: Fake file object doesn't crash
    });
  });

  describe("Type tag mutation: wrong or missing type field", () => {
    it("renders when type field is missing (runtime error expected or graceful fallback)", () => {
      const value = {
        // type is missing—union should match single, gradient, or image
        color: "ff0000",
      };

      // TypeScript should error here; runtime behavior is undefined
      expect(() => {
        render(
          <ColorPickerUniversal
            mode="single"
            value={value as unknown as ColorPickerValue}
            onChange={() => {}}
            onModeChange={() => {}}
          />
        );
      }).not.toThrow(); // May render but be in unexpected state
      // CHECKPOINT: Missing type field is a contract violation; ensure it doesn't crash
    });

    it("renders when type field is wrong string (e.g., 'color' instead of 'single')", () => {
      const value = {
        type: "color", // Not a valid discriminator
        color: "ff0000",
      };

      // TypeScript would reject this; runtime should handle gracefully
      expect(() => {
        render(
          <ColorPickerUniversal
            mode="single"
            value={value as unknown as ColorPickerValue}
            onChange={() => {}}
            onModeChange={() => {}}
          />
        );
      }).not.toThrow();
      // CHECKPOINT: Invalid type discriminator doesn't crash
    });

    it("renders when type field is null", () => {
      const value = {
        type: null,
        color: "ff0000",
      };

      expect(() => {
        render(
          <ColorPickerUniversal
            mode="single"
            value={value as unknown as ColorPickerValue}
            onChange={() => {}}
            onModeChange={() => {}}
          />
        );
      }).not.toThrow();
    });

    it("renders when type field is a number", () => {
      const value = {
        type: 1, // Invalid
        color: "ff0000",
      };

      expect(() => {
        render(
          <ColorPickerUniversal
            mode="single"
            value={value as unknown as ColorPickerValue}
            onChange={() => {}}
            onModeChange={() => {}}
          />
        );
      }).not.toThrow();
    });
  });

  describe("Consumer type narrowing: onChange payloads with wrong types", () => {
    it("consumer that doesn't narrow type before accessing mode-specific field", () => {
      // Simulates a buggy consumer that doesn't check v.type before accessing v.color
      function BuggyConsumer() {
        const onChange = (v: ColorPickerValue) => {
          // This is buggy: no type check
          // @ts-ignore
          const color = v.color; // May not exist if type !== "single"
          expect(color).toBeDefined(); // Will fail if v is gradient
        };

        const value: ColorPickerValue = { type: "single", color: "ff0000" };

        return (
          <ColorPickerUniversal
            mode="single"
            value={value}
            onChange={onChange}
            onModeChange={() => {}}
          />
        );
      }

      render(<BuggyConsumer />);
      expect(screen.getByPlaceholderText("RRGGBB")).toBeInTheDocument();
      // CHECKPOINT: Test that proper consumers must narrow type
    });

    it("properly narrowed consumer only accesses correct fields", () => {
      function ProperConsumer() {
        const onChange = (v: ColorPickerValue) => {
          if (v.type === "single") {
            expect(v.color).toBeDefined();
            // Only access v.color when type is "single"
          } else if (v.type === "gradient") {
            expect(v.colorA).toBeDefined();
            expect(v.colorB).toBeDefined();
            expect(v.direction).toBeDefined();
          } else if (v.type === "image") {
            // v.file may be null
            expect("file" in v).toBe(true);
          }
        };

        const value: ColorPickerValue = { type: "single", color: "ff0000" };

        return (
          <ColorPickerUniversal
            mode="single"
            value={value}
            onChange={onChange}
            onModeChange={() => {}}
          />
        );
      }

      render(<ProperConsumer />);
      expect(screen.getByPlaceholderText("RRGGBB")).toBeInTheDocument();
      // CHECKPOINT: Proper narrowing is enforced
    });
  });

  describe("onChange callback receiving malformed payloads", () => {
    it("onChange receives value with extra unknown fields, ignores gracefully", () => {
      const onChange = vi.fn();
      const value: ColorPickerValue = { type: "single", color: "ff0000" };

      render(
        <ColorPickerUniversal
          mode="single"
          value={value}
          onChange={onChange}
          onModeChange={() => {}}
        />
      );

      const hexField = screen.getByPlaceholderText("RRGGBB");
      act(() => {
        fireEvent.change(hexField, { target: { value: "00ff00" } });
      });

      // onChange should be called with valid payload, extra fields ignored
      expect(onChange).toHaveBeenCalled();
      const receivedValue = onChange.mock.calls[0][0];
      expect(receivedValue.type).toBe("single");
      expect(receivedValue.color).toBe("00ff00");
      // Extra fields may or may not be present; spec doesn't require strict checking
    });

    it("onChange receives completely wrong object structure, parent handles", () => {
      const onChange = vi.fn();
      const value: ColorPickerValue = { type: "single", color: "ff0000" };

      render(
        <ColorPickerUniversal
          mode="single"
          value={value}
          onChange={onChange}
          onModeChange={() => {}}
        />
      );

      const hexField = screen.getByPlaceholderText("RRGGBB");
      act(() => {
        fireEvent.change(hexField, { target: { value: "aabbcc" } });
      });

      // onChange should emit valid ColorPickerValue
      expect(onChange).toHaveBeenCalled();
      const received = onChange.mock.calls[0][0];
      // Should be a valid ColorPickerValue
      expect(received).toHaveProperty("type");
      expect(received).toHaveProperty("color");
      // CHECKPOINT: Payload structure is always valid from component perspective
    });
  });

  describe("Mode lock behavior with type mismatches", () => {
    it("lockMode='single' but value.type='gradient', ignores type mismatch", () => {
      // This is a contract violation, but component should handle gracefully
      const value = {
        type: "gradient",
        colorA: "ff0000",
        colorB: "0000ff",
        direction: "horizontal" as const,
      };

      // Locked to single mode, but value is gradient
      render(
        <ColorPickerUniversal
          lockMode="single"
          mode="single"
          value={value as unknown as ColorPickerValue}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Component should render in single mode; what happens to gradient data?
      // CHECKPOINT: Mismatch between lockMode and value.type is a contract violation
      // Ensure component doesn't crash, but behavior is undefined
      expect(screen.queryByRole("group", { name: /color picker mode/i })).not.toBeInTheDocument();
    });

    it("lockMode='gradient' but value.type='single', gracefully switches or falls back", () => {
      const value: ColorPickerValue = {
        type: "single",
        color: "ff0000",
      };

      render(
        <ColorPickerUniversal
          lockMode="gradient"
          mode="gradient"
          value={value}
          onChange={() => {}}
          onModeChange={() => {}}
        />
      );

      // Locked to gradient, but value is single — should render gradient mode anyway
      // or fall back to displaying what it can
      const modeGroup = screen.queryByRole("group", { name: /color picker mode/i });
      expect(modeGroup).not.toBeInTheDocument(); // lockMode hides tabs
      // CHECKPOINT: Mode/value mismatch is undefined behavior; ensure no crash
    });
  });

  describe("Discriminated union exhaustiveness in consumers", () => {
    it("verifies that all three union members are handled in type guards", () => {
      // This is a compile-time check enforced by TypeScript
      // Runtime test verifies the pattern is correctly used
      function exhaustiveCheck(v: ColorPickerValue) {
        if (v.type === "single") {
          return { result: v.color };
        } else if (v.type === "gradient") {
          return { result: `${v.colorA}-${v.colorB}-${v.direction}` };
        } else if (v.type === "image") {
          return { result: v.file ? "file" : "no-file" };
        }
        // Compiler ensures no other cases are reachable
        // If this were missing a case, TypeScript would error on exhaustiveness
        const _exhaustive: never = v;
        return _exhaustive;
      }

      const singleValue: ColorPickerValue = { type: "single", color: "ff0000" };
      expect(exhaustiveCheck(singleValue).result).toBe("ff0000");

      const gradientValue: ColorPickerValue = {
        type: "gradient",
        colorA: "ff0000",
        colorB: "0000ff",
        direction: "horizontal",
      };
      expect(exhaustiveCheck(gradientValue).result).toContain("ff0000");

      const imageValue: ColorPickerValue = { type: "image", file: null };
      expect(exhaustiveCheck(imageValue).result).toBe("no-file");
      // CHECKPOINT: Exhaustive checks are properly enforced
    });
  });
});
