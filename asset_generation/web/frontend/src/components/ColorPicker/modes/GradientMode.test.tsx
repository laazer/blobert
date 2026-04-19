// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { GradientMode } from "./GradientMode";

afterEach(() => {
  cleanup();
});

describe("GradientMode", () => {
  it("renders two hex input fields", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    const inputs = screen.getAllByPlaceholderText("RRGGBB");
    expect(inputs).toHaveLength(2);
  });

  it("displays correct colors in input fields", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="00ff00"
        direction="vertical"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    const inputs = screen.getAllByPlaceholderText("RRGGBB");
    expect((inputs[0] as HTMLInputElement).value).toBe("ff0000");
    expect((inputs[1] as HTMLInputElement).value).toBe("00ff00");
  });

  it("calls onColorAChange when first color changes", async () => {
    const onColorAChange = vi.fn();
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={onColorAChange}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    const inputs = screen.getAllByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(inputs[0], { target: { value: "ffff00" } });
    });

    expect(onColorAChange).toHaveBeenCalledWith("ffff00");
  });

  it("calls onColorBChange when second color changes", async () => {
    const onColorBChange = vi.fn();
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={onColorBChange}
        onDirectionChange={() => {}}
      />
    );

    const inputs = screen.getAllByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(inputs[1], { target: { value: "00ff00" } });
    });

    expect(onColorBChange).toHaveBeenCalledWith("00ff00");
  });

  it("calls onDirectionChange when direction button is clicked", async () => {
    const onDirectionChange = vi.fn();
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={onDirectionChange}
      />
    );

    const buttons = screen.getAllByRole("button").filter((btn) =>
      ["→", "↓", "◯"].some((symbol) => btn.textContent?.includes(symbol))
    );

    await act(async () => {
      fireEvent.click(buttons[1]); // vertical button
    });

    expect(onDirectionChange).toHaveBeenCalledWith("vertical");
  });

  it("renders labels for both colors", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    expect(screen.getByText("From Color")).toBeInTheDocument();
    expect(screen.getByText("To Color")).toBeInTheDocument();
  });

  it("disables all controls when disabled prop is true", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
        disabled={true}
      />
    );

    const inputs = screen.getAllByPlaceholderText("RRGGBB");
    inputs.forEach((input) => {
      expect((input as HTMLInputElement).disabled).toBe(true);
    });
  });

  it("renders direction selector", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    expect(screen.getByText("Direction")).toBeInTheDocument();
  });

  it("shows copy buttons for both colors", () => {
    render(
      <GradientMode
        colorA="ff0000"
        colorB="0000ff"
        direction="horizontal"
        onColorAChange={() => {}}
        onColorBChange={() => {}}
        onDirectionChange={() => {}}
      />
    );

    const copyButtons = screen.getAllByRole("button", { name: /copy/i });
    expect(copyButtons.length).toBeGreaterThanOrEqual(2);
  });
});
