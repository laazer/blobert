// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { SingleColorMode } from "./SingleColorMode";

afterEach(() => {
  cleanup();
});

describe("SingleColorMode", () => {
  it("renders hex input field", () => {
    render(
      <SingleColorMode
        color="ff0000"
        onChange={() => {}}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    expect(input).toBeInTheDocument();
  });

  it("displays current color value in input", () => {
    render(
      <SingleColorMode
        color="00ff00"
        onChange={() => {}}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.value).toBe("00ff00");
  });

  it("calls onChange when color changes", async () => {
    const onChange = vi.fn();
    render(
      <SingleColorMode
        color="ff0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(input, { target: { value: "0000ff" } });
    });

    expect(onChange).toHaveBeenCalledWith("0000ff");
  });

  it("renders copy button", () => {
    render(
      <SingleColorMode
        color="ff0000"
        onChange={() => {}}
      />
    );

    const copyButton = screen.getByRole("button", { name: /copy/i });
    expect(copyButton).toBeInTheDocument();
  });

  it("disables input when disabled prop is true", () => {
    render(
      <SingleColorMode
        color="ff0000"
        onChange={() => {}}
        disabled={true}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it("shows label 'Color'", () => {
    render(
      <SingleColorMode
        color="ff0000"
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Color")).toBeInTheDocument();
  });

  it("updates displayed value when color prop changes", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <SingleColorMode
        color="ff0000"
        onChange={onChange}
      />
    );

    let input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.value).toBe("ff0000");

    rerender(
      <SingleColorMode
        color="00ff00"
        onChange={onChange}
      />
    );

    input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.value).toBe("00ff00");
  });
});
