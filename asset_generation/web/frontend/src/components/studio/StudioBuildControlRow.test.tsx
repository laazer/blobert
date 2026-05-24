// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { StudioBuildControlRow } from "./StudioBuildControlRow";

afterEach(() => cleanup());

describe("StudioBuildControlRow", () => {
  it("renders segmented pills for eye_count even when meta type is int", () => {
    const def: AnimatedBuildControlDef = {
      key: "eye_count",
      label: "Eyes",
      type: "int",
      min: 1,
      max: 8,
      default: 2,
    };
    const onChange = vi.fn();
    render(
      <StudioBuildControlRow def={def} value={2} accentHue="#ff6b3d" onChange={onChange} />,
    );
    expect(screen.getByTestId("studio-build-segmented-eye_count")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "4" }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("renders segmented pills for eye_count select", () => {
    const def: AnimatedBuildControlDef = {
      key: "eye_count",
      label: "Count",
      type: "select",
      options: [1, 2, 3, 4],
      default: 2,
    };
    const onChange = vi.fn();
    render(
      <StudioBuildControlRow def={def} value={2} accentHue="#ff6b3d" onChange={onChange} />,
    );
    expect(screen.getByTestId("studio-build-segmented-eye_count")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "4" }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("renders slider for float defs", () => {
    const def: AnimatedBuildControlDef = {
      key: "stripe_width",
      label: "Stripe width",
      type: "float",
      min: 0,
      max: 1,
      step: 0.05,
      default: 0.4,
    };
    render(
      <StudioBuildControlRow def={def} value={0.4} accentHue="#ff6b3d" onChange={vi.fn()} />,
    );
    expect(screen.getByTestId("studio-build-slider-stripe_width")).toBeInTheDocument();
    expect(screen.getByText("Stripe width")).toBeInTheDocument();
  });
});
