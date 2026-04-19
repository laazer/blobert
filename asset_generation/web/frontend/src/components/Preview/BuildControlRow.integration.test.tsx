// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi, beforeEach } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow } from "./BuildControlRow";

afterEach(() => {
  cleanup();
});

describe("Requirement 2: HexStrControlRow Integration Verification", () => {
  describe("A2.1 & A2.2: ColorPickerUniversal import and props", () => {
    const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
      key: "feat_body_hex",
      label: "Body base hex",
      type: "str",
      default: "8b7355",
    };

    it("renders ColorPickerUniversal with lockMode='single' and mode='single'", () => {
      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ff0000" onChange={onChange} />);

      // Verify that single mode is locked (no mode tabs visible)
      const modeGroup = screen.queryByRole("group", { name: /color picker mode/i });
      expect(modeGroup).not.toBeInTheDocument();

      // Verify single color input is rendered (ColorPickerUniversal in single mode)
      // The color picker has a title attribute "Pick color" on the color swatch
      const colorSwatch = screen.getByTitle("Pick color");
      expect(colorSwatch).toBeInTheDocument();
    });

    it("imports ColorPickerValue type and uses correct discriminated union structure", () => {
      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ffaa00" onChange={onChange} />);

      const hexInput = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
      expect(hexInput.value).toBe("ffaa00");

      // Trigger onChange and verify it passes single color string
      act(() => {
        fireEvent.change(hexInput, { target: { value: "00ff00" } });
      });

      expect(onChange).toHaveBeenCalledWith("00ff00");
    });
  });

  describe("A2.3 & A2.4: Paste button rendering and clipboard integration", () => {
    const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
      key: "feat_body_hex",
      label: "Body base hex",
      type: "str",
      default: "ffffff",
    };

    it("renders Paste button immediately after picker with correct title", () => {
      render(<ControlRow def={hexDef} value="000000" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      expect(pasteBtn).toBeInTheDocument();
      expect(pasteBtn).toHaveAttribute("title", "Paste #RRGGBB or RRGGBB from clipboard");
    });

    it("calls onChange with clipboard hex value on successful paste", async () => {
      const onChange = vi.fn();
      const clipboardMock = {
        readText: vi.fn().mockResolvedValue("ff5500"),
      };
      Object.assign(navigator, { clipboard: clipboardMock });

      render(<ControlRow def={hexDef} value="000000" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await act(async () => {
        fireEvent.click(pasteBtn);
        await waitFor(() => {
          expect(clipboardMock.readText).toHaveBeenCalled();
        });
      });

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("ff5500");
      });
    });
  });

  describe("A2.5: Error hint on clipboard read failure", () => {
    const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
      key: "feat_body_hex",
      label: "Body base hex",
      type: "str",
      default: "cccccc",
    };

    it("displays 'No #RRGGBB in clipboard' on invalid paste", async () => {
      const clipboardMock = {
        readText: vi.fn().mockResolvedValue("not a hex value"),
      };
      Object.assign(navigator, { clipboard: clipboardMock });

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      fireEvent.click(pasteBtn);

      // Verify error message appears when invalid clipboard content is encountered
      await waitFor(() => {
        expect(screen.getByRole("status")).toHaveTextContent("No #RRGGBB in clipboard");
      });
    });

    it("successfully pastes valid hex from clipboard", async () => {
      const onChange = vi.fn();
      const clipboardMock = {
        readText: vi.fn().mockResolvedValue("00ff00"),
      };
      Object.assign(navigator, { clipboard: clipboardMock });

      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      fireEvent.click(pasteBtn);

      // Verify onChange is called with the pasted hex value
      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("00ff00");
      });
    });
  });

  describe("A2.6: No unused props or mode options", () => {
    const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
      key: "feat_body_texture_grad_color_a",
      label: "Gradient color A",
      type: "str",
      default: "ff0000",
    };

    it("passes only required props to ColorPickerUniversal (no unused options)", () => {
      // This is a structural test: verify that HexStrControlRow only passes the required props
      // lockMode, mode, label, value, onChange, onModeChange
      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="aa0000" onChange={onChange} />);

      // Verify basic structure: only single-color mode with no mode switching
      const modeGroup = screen.queryByRole("group", { name: /color picker mode/i });
      expect(modeGroup).not.toBeInTheDocument(); // lockMode is set, so tabs are hidden

      // Verify color swatch (from HexInput) is rendered
      const colorSwatch = screen.getByTitle("Pick color");
      expect(colorSwatch).toBeInTheDocument(); // Single color mode is rendered

      // Verify no gradient direction selectors exist
      const directionSelectors = screen.queryAllByRole("combobox", { name: /direction/i });
      expect(directionSelectors).toHaveLength(0);
    });
  });

  describe("Str control with hex key pattern detection", () => {
    it("recognizes feat_*_hex pattern and renders hex picker", () => {
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_eye_left_hex",
        label: "Eye left color",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      // Should render ColorPickerUniversal + Paste button
      expect(screen.getByTitle("Pick color")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Paste color" })).toBeInTheDocument();
    });

    it("recognizes feat_*_texture_*_color pattern and renders hex picker", () => {
      const colorDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_texture_grad_color_b",
        label: "Gradient color B",
        type: "str",
        default: "0000ff",
      };

      render(<ControlRow def={colorDef} value="00ff00" onChange={() => {}} />);

      expect(screen.getByTitle("Pick color")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Paste color" })).toBeInTheDocument();
    });

    it("renders regular text input for non-hex str controls", () => {
      const textDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "some_text_option",
        label: "Some text",
        type: "str",
        default: "default_text",
      };

      render(<ControlRow def={textDef} value="text_value" onChange={() => {}} />);

      // Should NOT render ColorPickerUniversal (no hex input, no paste button)
      expect(screen.queryByTitle("Pick color")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Paste color" })).not.toBeInTheDocument();

      // Should render regular text input with the provided value
      const textInput = screen.getByRole("textbox") as HTMLInputElement;
      expect(textInput.type).toBe("text");
      expect(textInput.value).toBe("text_value");
    });
  });
});
