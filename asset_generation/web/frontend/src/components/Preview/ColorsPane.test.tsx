// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
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
});
