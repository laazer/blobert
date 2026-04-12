// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { GlbViewer } from "./GlbViewer";

describe("GlbViewer expand/collapse", () => {
  beforeEach(() => {
    useAppStore.setState({ activeGlbUrl: null, activeAnimation: null });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders with Expand viewer button and aria-pressed false", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });

  it("button is always enabled regardless of browser API support", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));
    expect(btn).not.toBeDisabled();
  });

  it("button text reads 'Fullscreen' when not expanded", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));
    expect(btn).toHaveTextContent("Fullscreen");
  });

  it("clicking expand toggles aria-pressed to true and changes label to Collapse viewer", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));

    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Collapse viewer" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Collapse viewer" })).toHaveAttribute("aria-pressed", "true");
  });

  it("button text reads 'Exit fullscreen' when expanded", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));

    fireEvent.click(btn);

    await waitFor(() => {
      const collapseBtn = screen.getByRole("button", { name: "Collapse viewer" });
      expect(collapseBtn).toHaveTextContent("Exit fullscreen");
    });
  });

  it("clicking collapse restores button to Expand viewer state", async () => {
    render(<GlbViewer />);
    const expandBtn = await waitFor(() => screen.getByRole("button", { name: "Expand viewer" }));

    fireEvent.click(expandBtn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Collapse viewer" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Collapse viewer" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Expand viewer" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Expand viewer" })).toHaveAttribute("aria-pressed", "false");
  });
});
