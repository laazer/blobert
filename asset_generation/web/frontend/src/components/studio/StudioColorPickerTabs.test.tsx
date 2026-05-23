// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import { StudioColorPickerTabs } from "./StudioColorPickerTabs";

afterEach(() => {
  cleanup();
});

describe("StudioColorPickerTabs", () => {
  it("renders studio tab labels and hex row", () => {
    const onChange = vi.fn();
    render(
      <StudioColorPickerTabs
        accentHue="#ff6b3d"
        mode="single"
        value={{ type: "single", color: "ffd23d" }}
        onModeChange={vi.fn()}
        onChange={onChange}
        paletteColors={["#ffd23d", "#e6531f"]}
        onPaletteColorPick={vi.fn()}
      />,
    );

    expect(screen.getByTestId("studio-color-picker-tabs")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Color" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Image" })).toBeInTheDocument();
    expect(screen.getByText("#ffd23d")).toBeInTheDocument();
  });

  it("calls onModeChange when switching tabs", () => {
    const onModeChange = vi.fn();
    render(
      <StudioColorPickerTabs
        accentHue="#ff6b3d"
        mode="single"
        value={{ type: "single", color: "ffffff" }}
        onModeChange={onModeChange}
        onChange={vi.fn()}
      />,
    );

    const tabs = within(screen.getByTestId("studio-color-picker-tabs"));
    fireEvent.click(tabs.getByRole("tab", { name: "Gradient" }));
    expect(onModeChange).toHaveBeenCalledWith("gradient");
  });
});
