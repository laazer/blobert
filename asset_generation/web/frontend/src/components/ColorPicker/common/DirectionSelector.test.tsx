// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { DirectionSelector } from "./DirectionSelector";

afterEach(() => {
  cleanup();
});

describe("DirectionSelector", () => {
  it("renders three direction buttons", () => {
    render(
      <DirectionSelector
        direction="horizontal"
        onChange={() => {}}
      />
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(3);
  });

  it("marks current direction as pressed", () => {
    render(
      <DirectionSelector
        direction="vertical"
        onChange={() => {}}
      />
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons[1]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "false");
    expect(buttons[2]).toHaveAttribute("aria-pressed", "false");
  });

  it("calls onChange when direction button is clicked", async () => {
    const onChange = vi.fn();
    render(
      <DirectionSelector
        direction="horizontal"
        onChange={onChange}
      />
    );

    const buttons = screen.getAllByRole("button");
    await act(async () => {
      fireEvent.click(buttons[1]); // vertical button
    });

    expect(onChange).toHaveBeenCalledWith("vertical");
  });

  it("renders direction label", () => {
    render(
      <DirectionSelector
        direction="horizontal"
        onChange={() => {}}
      />
    );

    expect(screen.getByText("Direction")).toBeInTheDocument();
  });

  it("disables all buttons when disabled prop is true", () => {
    render(
      <DirectionSelector
        direction="horizontal"
        onChange={() => {}}
        disabled={true}
      />
    );

    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("updates pressed state when direction changes", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <DirectionSelector
        direction="horizontal"
        onChange={onChange}
      />
    );

    let buttons = screen.getAllByRole("button");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "true");

    rerender(
      <DirectionSelector
        direction="radial"
        onChange={onChange}
      />
    );

    buttons = screen.getAllByRole("button");
    expect(buttons[2]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "false");
  });

  it("renders direction symbols", () => {
    const { container } = render(
      <DirectionSelector
        direction="horizontal"
        onChange={() => {}}
      />
    );

    expect(container.textContent).toContain("→");
    expect(container.textContent).toContain("↓");
    expect(container.textContent).toContain("◯");
  });
});
