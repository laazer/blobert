// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { cleanup, render, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { BuildControls } from "./BuildControls";

describe("BuildControls preview URL sync", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: { spider: {} },
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("does not call selectAssetByPath when preview already shows default variant path", async () => {
    const fixed = "/api/assets/animated_exports/spider_animated_00.glb?t=999";
    useAppStore.setState({ activeGlbUrl: fixed });
    render(<BuildControls />);
    await waitFor(() => {
      expect(useAppStore.getState().activeGlbUrl).toBe(fixed);
    });
  });

  it("selects default variant when preview path differs", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_02.glb?t=1",
    });
    render(<BuildControls />);
    await waitFor(() => {
      const url = useAppStore.getState().activeGlbUrl;
      expect(url).toMatch(/^\/api\/assets\/animated_exports\/spider_animated_00\.glb\?t=\d+$/);
      expect(url).not.toBe("/api/assets/animated_exports/spider_animated_02.glb?t=1");
    });
  });
});
