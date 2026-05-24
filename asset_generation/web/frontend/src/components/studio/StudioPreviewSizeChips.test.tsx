// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { StudioPreviewSizeChips } from "./StudioPreviewSizeChips";

afterEach(() => {
  cleanup();
});

describe("StudioPreviewSizeChips", () => {
  it("calls shrink and enlarge handlers", () => {
    const onShrink = vi.fn();
    const onEnlarge = vi.fn();
    render(
      <StudioPreviewSizeChips
        scale={0.8}
        canShrink
        canEnlarge
        onShrink={onShrink}
        onEnlarge={onEnlarge}
      />,
    );
    expect(screen.getByTestId("studio-preview-scale-label")).toHaveTextContent("80%");
    fireEvent.click(screen.getByTestId("studio-preview-shrink"));
    fireEvent.click(screen.getByTestId("studio-preview-enlarge"));
    expect(onShrink).toHaveBeenCalledTimes(1);
    expect(onEnlarge).toHaveBeenCalledTimes(1);
  });

  it("disables buttons at scale limits", () => {
    render(
      <StudioPreviewSizeChips
        scale={1}
        canShrink={false}
        canEnlarge={false}
        onShrink={vi.fn()}
        onEnlarge={vi.fn()}
      />,
    );
    expect(screen.getByTestId("studio-preview-shrink")).toBeDisabled();
    expect(screen.getByTestId("studio-preview-enlarge")).toBeDisabled();
  });
});
