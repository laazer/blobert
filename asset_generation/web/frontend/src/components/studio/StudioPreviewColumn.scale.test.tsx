// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { StudioPreviewColumn } from "./StudioPreviewColumn";
import { STUDIO_PREVIEW_SCALE_LS } from "../../utils/studioPreviewScale";

vi.mock("../Preview/GlbViewer", () => ({ GlbViewer: () => <div data-testid="glb-viewer" /> }));
vi.mock("../Preview/AnimationControls", () => ({
  AnimationControls: () => <div data-testid="animation-controls" />,
}));
vi.mock("./StudioPreviewMetaBar", () => ({
  StudioPreviewMetaBar: () => null,
}));

afterEach(() => {
  cleanup();
  localStorage.removeItem(STUDIO_PREVIEW_SCALE_LS);
});

describe("StudioPreviewColumn preview scale", () => {
  beforeEach(() => {
    localStorage.setItem(STUDIO_PREVIEW_SCALE_LS, "1");
  });

  it("defaults viewport to 80% size", () => {
    localStorage.removeItem(STUDIO_PREVIEW_SCALE_LS);
    render(<StudioPreviewColumn />);
    const viewport = screen.getByTestId("studio-preview-viewport");
    expect(viewport).toHaveStyle({ width: "80%", height: "80%" });
    expect(screen.getByTestId("studio-preview-scale-label")).toHaveTextContent("80%");
  });

  it("enlarges viewport when + chip is clicked", () => {
    render(<StudioPreviewColumn />);
    fireEvent.click(screen.getByTestId("studio-preview-enlarge"));
    const viewport = screen.getByTestId("studio-preview-viewport");
    expect(viewport).toHaveStyle({ width: "100%", height: "100%" });
    expect(screen.getByTestId("studio-preview-scale-label")).toHaveTextContent("100%");
  });
});
