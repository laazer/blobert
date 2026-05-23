// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import { StudioColorPickerTabs } from "./StudioColorPickerTabs";

vi.mock("../../api/client", () => ({
  fetchTextureAssets: vi.fn().mockResolvedValue([
    { id: "tex-a", url: "/tex-a.png", display_name: "Spots A" },
    { id: "tex-b", url: "/tex-b.png", display_name: "Stripes B" },
  ]),
}));

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

  it("renders studio gradient preview and direction pills", () => {
    render(
      <StudioColorPickerTabs
        accentHue="#ff6b3d"
        mode="gradient"
        value={{ type: "gradient", colorA: "ff0000", colorB: "0000ff", direction: "horizontal" }}
        onModeChange={vi.fn()}
        onChange={vi.fn()}
        paletteColors={["#ff0000", "#0000ff"]}
      />,
    );

    expect(screen.getByTestId("studio-gradient-mode")).toBeInTheDocument();
    expect(screen.getByText("Stop 1")).toBeInTheDocument();
    expect(screen.getByTestId("studio-gradient-dir-radial")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "copy" }).length).toBeGreaterThanOrEqual(2);
  });

  it("renders studio image library when image tab active", async () => {
    render(
      <StudioColorPickerTabs
        accentHue="#ff6b3d"
        mode="image"
        value={{ type: "image", preview: "/tex-a.png", assetId: "tex-a" }}
        onModeChange={vi.fn()}
        onChange={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("studio-image-mode")).toBeInTheDocument();
    expect(screen.getByTestId("studio-image-preview")).toBeInTheDocument();
    expect(screen.getByTestId("studio-image-hero-crop")).toBeInTheDocument();
    expect(screen.getByLabelText("Zoom in")).toBeInTheDocument();
    expect(screen.getByText("Library")).toBeInTheDocument();
    expect(screen.getByTestId("studio-texture-tex-a")).toBeInTheDocument();
  });
});
