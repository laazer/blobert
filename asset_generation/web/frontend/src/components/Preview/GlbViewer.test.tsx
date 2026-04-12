// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { GlbViewer } from "./GlbViewer";

describe("GlbViewer fullscreen", () => {
  let origRequestFullscreen: typeof HTMLElement.prototype.requestFullscreen;
  let origExitFullscreen: typeof Document.prototype.exitFullscreen;
  let fullscreenEl: Element | null = null;
  let exitFullscreenSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    useAppStore.setState({ activeGlbUrl: null, activeAnimation: null });
    origRequestFullscreen = HTMLElement.prototype.requestFullscreen;
    origExitFullscreen = Document.prototype.exitFullscreen;
    fullscreenEl = null;

    Object.defineProperty(document, "fullscreenEnabled", { value: true, configurable: true });
    Object.defineProperty(document, "fullscreenElement", {
      configurable: true,
      get: () => fullscreenEl,
    });

    HTMLElement.prototype.requestFullscreen = function mockRequestFullscreen(this: HTMLElement) {
      fullscreenEl = this;
      return Promise.resolve();
    };

    exitFullscreenSpy = vi.fn(() => {
      fullscreenEl = null;
      return Promise.resolve();
    });
    document.exitFullscreen = exitFullscreenSpy as typeof Document.prototype.exitFullscreen;
  });

  afterEach(() => {
    cleanup();
    HTMLElement.prototype.requestFullscreen = origRequestFullscreen;
    document.exitFullscreen = origExitFullscreen;
    vi.restoreAllMocks();
  });

  it("toggle calls requestFullscreen then exitFullscreen on the viewer wrapper", async () => {
    render(<GlbViewer />);

    const btn = await waitFor(() => screen.getByRole("button", { name: "Enter fullscreen" }));
    expect(btn).not.toBeDisabled();
    const viewerWrap = btn.parentElement;
    expect(viewerWrap).toBeTruthy();

    fireEvent.click(btn);

    await waitFor(() => {
      expect(fullscreenEl).toBe(viewerWrap);
    });

    document.dispatchEvent(new Event("fullscreenchange"));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Exit fullscreen" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Exit fullscreen" }));

    await waitFor(() => {
      expect(exitFullscreenSpy).toHaveBeenCalled();
    });
    document.dispatchEvent(new Event("fullscreenchange"));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Enter fullscreen" })).toBeTruthy();
    });
  });

  it("uses aria-pressed false when not fullscreen", async () => {
    render(<GlbViewer />);
    const btn = await waitFor(() => screen.getByRole("button", { name: "Enter fullscreen" }));
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });
});
