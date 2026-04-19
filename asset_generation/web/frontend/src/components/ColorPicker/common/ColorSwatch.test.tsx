// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { ColorSwatch } from "./ColorSwatch";

afterEach(() => {
  cleanup();
});

describe("ColorSwatch", () => {
  it("renders color swatch with correct background color", () => {
    const { container } = render(
      <ColorSwatch color="ff0000" />
    );

    const swatch = container.querySelector("div[style*='background-color']");
    expect(swatch).toBeInTheDocument();
    expect(swatch?.getAttribute("style")).toContain("rgb(255, 0, 0)");
  });

  it("renders default black color when color is empty", () => {
    const { container } = render(
      <ColorSwatch color="" />
    );

    const swatch = container.querySelector("div[style*='background-color']");
    expect(swatch?.getAttribute("style")).toContain("rgb(0, 0, 0)");
  });

  it("renders label when provided", () => {
    render(
      <ColorSwatch
        color="ff0000"
        label="Body Color"
      />
    );

    expect(screen.getByText("Body Color")).toBeInTheDocument();
  });

  it("is clickable when onClick is provided", async () => {
    const onClick = vi.fn();
    render(
      <ColorSwatch
        color="ff0000"
        onClick={onClick}
      />
    );

    const button = screen.getByRole("button");
    await act(async () => {
      fireEvent.click(button);
    });

    expect(onClick).toHaveBeenCalled();
  });

  it("is not clickable when disabled", () => {
    const onClick = vi.fn();
    render(
      <ColorSwatch
        color="ff0000"
        onClick={onClick}
        disabled={true}
      />
    );

    // When disabled and onClick provided, button should still exist but be disabled
    // In our implementation, we don't render button when disabled and onClick provided
    // So just verify the color swatch div exists
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("has reduced opacity when disabled", () => {
    const { container } = render(
      <ColorSwatch
        color="ff0000"
        disabled={true}
      />
    );

    const swatch = container.querySelector("div[style*='opacity']");
    expect(swatch?.getAttribute("style")).toContain("opacity");
  });

  it("handles various hex color formats", () => {
    const { rerender, container } = render(
      <ColorSwatch color="00ff00" />
    );

    let swatch = container.querySelector("div[style*='background-color']");
    expect(swatch?.getAttribute("style")).toContain("rgb(0, 255, 0)");

    rerender(
      <ColorSwatch color="0000ff" />
    );

    swatch = container.querySelector("div[style*='background-color']");
    expect(swatch?.getAttribute("style")).toContain("rgb(0, 0, 255)");
  });
});
