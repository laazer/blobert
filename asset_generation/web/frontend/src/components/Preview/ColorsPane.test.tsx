// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { ColorsPane } from "./ColorsPane";

afterEach(() => {
  cleanup();
});

describe("ColorsPane", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["slug"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "slug" },
      animatedEnemyMeta: [{ slug: "slug", label: "Slug" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: {
        slug: { feat_body_finish: "matte", feat_body_hex: "" },
      },
      centerPanel: "colors",
    });
  });

  it("shows empty-state when not animated enemy or player", () => {
    useAppStore.setState({ commandContext: { cmd: "level", enemy: "x" } });
    render(<ColorsPane />);
    expect(screen.getByText(/per-zone finishes/i)).toBeInTheDocument();
  });

  it("renders feature controls for player cmd using player_slime slug", () => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, [PLAYER_PROCEDURAL_BUILD_SLUG]);
    useAppStore.setState({
      commandContext: { cmd: "player", enemy: "blue" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: {
        [PLAYER_PROCEDURAL_BUILD_SLUG]: { feat_body_finish: "glossy", feat_body_hex: "" },
      },
      centerPanel: "colors",
    });
    render(<ColorsPane />);
    expect(screen.getByText(/Part materials/i)).toBeInTheDocument();
    expect(screen.getByText(/cheek blush/i)).toBeInTheDocument();
  });

  it("hydrates feat_* zone finishes from command export after microtask (ordering fix)", async () => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    const merged = mergeBuildOptionValues(controls, {});
    const bodyFinishBefore = merged.spider?.feat_body_finish;
    expect(bodyFinishBefore).toBe("default");

    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: merged,
      centerPanel: "colors",
      commandExportFinish: "glossy",
      commandExportHexColor: "",
    });

    render(<ColorsPane />);
    await act(async () => {
      await Promise.resolve();
    });

    expect(useAppStore.getState().animatedBuildOptionValues.spider?.feat_body_finish).toBe("glossy");
  });

  it("hydrates from command bar when meta has no defs (empty controls) and option map has no feat_* keys", async () => {
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: { spider: [] },
      animatedBuildOptionValues: { spider: {} },
      centerPanel: "colors",
      commandExportFinish: "glossy",
      commandExportHexColor: "#aabbcc",
    });

    render(<ColorsPane />);
    await act(async () => {
      await Promise.resolve();
    });

    const spider = useAppStore.getState().animatedBuildOptionValues.spider;
    expect(spider?.feat_body_finish).toBe("glossy");
    expect(spider?.feat_body_hex).toBe("aabbcc");
  });

  it("re-hydrates zones when command export changes while Colors stays open", async () => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    const merged = mergeBuildOptionValues(controls, {});

    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: merged,
      centerPanel: "colors",
      commandExportFinish: "default",
      commandExportHexColor: "",
    });

    render(<ColorsPane />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(useAppStore.getState().animatedBuildOptionValues.spider?.feat_body_finish).toBe("default");

    await act(async () => {
      useAppStore.setState({ commandExportFinish: "matte" });
      await Promise.resolve();
    });

    expect(useAppStore.getState().animatedBuildOptionValues.spider?.feat_body_finish).toBe("matte");
  });
});
