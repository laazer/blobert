// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { GlbViewer } from "./GlbViewer";

afterEach(() => {
  cleanup();
});

describe("GlbViewer stripes shader", () => {
  beforeEach(() => {
    useAppStore.setState({
      activeGlbUrl: null,
      activeAnimation: null,
      texture_mode: "none",
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
  });

  it("accepts stripes mode without throwing", async () => {
    render(<GlbViewer />);
    act(() => {
      useAppStore.setState({
        texture_mode: "stripes",
        texture_stripe_color: "ff0000",
        texture_stripe_bg_color: "ffffff",
        texture_stripe_width: 0.4,
      });
    });
    await waitFor(() => {
      expect(true).toBe(true);
    });
  });
});
