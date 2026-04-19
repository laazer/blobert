// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { useState } from "react";
import {
  ColorPickerUniversal,
  type ColorPickerValue,
} from "./ColorPickerUniversal";

afterEach(() => {
  cleanup();
});

describe("ColorPickerUniversal", () => {
  it("renders with single color mode selected", () => {
    const value: ColorPickerValue = { type: "single", color: "ff0000" };
    render(
      <ColorPickerUniversal
        mode="single"
        value={value}
        onChange={() => {}}
        onModeChange={() => {}}
      />
    );

    const colorButton = screen.getByRole("button", { name: /color/i, pressed: true });
    expect(colorButton).toBeInTheDocument();
  });

  it("renders with gradient mode selected", () => {
    const value: ColorPickerValue = {
      type: "gradient",
      colorA: "ff0000",
      colorB: "0000ff",
      direction: "horizontal",
    };
    render(
      <ColorPickerUniversal
        mode="gradient"
        value={value}
        onChange={() => {}}
        onModeChange={() => {}}
      />
    );

    const gradientButton = screen.getByRole("button", {
      name: /gradient/i,
      pressed: true,
    });
    expect(gradientButton).toBeInTheDocument();
  });

  it("renders with image mode selected", () => {
    const value: ColorPickerValue = { type: "image", file: null };
    render(
      <ColorPickerUniversal
        mode="image"
        value={value}
        onChange={() => {}}
        onModeChange={() => {}}
      />
    );

    const imageButton = screen.getByRole("button", { name: /image/i, pressed: true });
    expect(imageButton).toBeInTheDocument();
  });

  it("calls onModeChange when mode button is clicked", async () => {
    const onModeChange = vi.fn();
    const value: ColorPickerValue = { type: "single", color: "ff0000" };

    render(
      <ColorPickerUniversal
        mode="single"
        value={value}
        onChange={() => {}}
        onModeChange={onModeChange}
      />
    );

    const gradientButton = screen.getByRole("button", { name: /gradient/i });
    await act(async () => {
      gradientButton.click();
    });

    expect(onModeChange).toHaveBeenCalledWith("gradient");
  });

  it("disables mode buttons when disabled prop is true", () => {
    const value: ColorPickerValue = { type: "single", color: "ff0000" };
    render(
      <ColorPickerUniversal
        mode="single"
        value={value}
        onChange={() => {}}
        onModeChange={() => {}}
        disabled={true}
      />
    );

    const colorButton = screen.getByRole("button", { name: /color/i });
    expect(colorButton).toBeDisabled();

    const gradientButton = screen.getByRole("button", { name: /gradient/i });
    expect(gradientButton).toBeDisabled();

    const imageButton = screen.getByRole("button", { name: /image/i });
    expect(imageButton).toBeDisabled();
  });

  it("renders label when provided", () => {
    const value: ColorPickerValue = { type: "single", color: "ff0000" };
    render(
      <ColorPickerUniversal
        mode="single"
        value={value}
        onChange={() => {}}
        onModeChange={() => {}}
        label="Pick a color"
      />
    );

    expect(screen.getByText("Pick a color")).toBeInTheDocument();
  });

  it("calls onChange when single-mode hex text changes", async () => {
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
    await act(async () => {
      fireEvent.change(hexField, { target: { value: "00ff00" } });
    });

    expect(onChange).toHaveBeenCalledWith({ type: "single", color: "00ff00" });
  });

  it("preserves inactive mode values when parent switches mode (controlled pattern)", async () => {
    function Harness() {
      const [mode, setMode] = useState<"single" | "gradient" | "image">("single");
      const [single, setSingle] = useState({ color: "ff0000" });
      const [gradient, setGradient] = useState({
        colorA: "111111",
        colorB: "222222",
        direction: "vertical" as const,
      });
      const [image, setImage] = useState<{ file: File | null; preview?: string }>({
        file: null,
      });

      const value: ColorPickerValue =
        mode === "single"
          ? { type: "single", ...single }
          : mode === "gradient"
            ? { type: "gradient", ...gradient }
            : { type: "image", ...image };

      return (
        <ColorPickerUniversal
          mode={mode}
          value={value}
          onModeChange={(m) => setMode(m)}
          onChange={(v) => {
            if (v.type === "single") setSingle({ color: v.color });
            else if (v.type === "gradient")
              setGradient({
                colorA: v.colorA,
                colorB: v.colorB,
                direction: v.direction,
              });
            else setImage({ file: v.file, preview: v.preview });
          }}
        />
      );
    }

    render(<Harness />);

    const modeGroup = screen.getByRole("group", { name: /color picker mode/i });

    await act(async () => {
      fireEvent.click(within(modeGroup).getByRole("button", { name: "Gradient" }));
    });

    expect(screen.getAllByPlaceholderText("RRGGBB")).toHaveLength(2);

    await act(async () => {
      fireEvent.click(within(modeGroup).getByRole("button", { name: "Color" }));
    });

    const hexAfter = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(hexAfter.value).toBe("ff0000");
  });
});
