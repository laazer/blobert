// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import type { AnimatedBuildControlDef } from "../../types";
import { BuildControls } from "./BuildControls";

// M25-04 — RIG_ naming convention is sufficient for rotation controls to appear in the Rig section.
//
// BuildControls.tsx line ~359 filters float controls with `d.key.startsWith("RIG_")`:
//   const rigFloats = allFloats.filter((d) => d.key.startsWith("RIG_"));
//
// The backend serves the following rotation controls for per-part rotation (M25-04):
//   RIG_HEAD_ROT_X, RIG_HEAD_ROT_Y, RIG_HEAD_ROT_Z
//   RIG_BODY_ROT_X, RIG_BODY_ROT_Y, RIG_BODY_ROT_Z
//
// Because these keys begin with "RIG_", they are automatically routed into the Rig section
// by the existing filter — no code change was needed to BuildControls.tsx for M25-04.
// The naming convention alone is sufficient; the pre-existing filter handles placement.

const noopLoad = vi.fn(() => Promise.resolve());

function stubLoad(fn: typeof noopLoad) {
  return fn as ReturnType<typeof useAppStore.getState>["loadAnimatedEnemyMeta"];
}

function emptyMetaContext(enemy: string) {
  return {
    commandContext: { cmd: "animated" as const, enemy },
    animatedEnemyMeta: [{ slug: enemy, label: "X" }],
    animatedBuildControls: {} as Record<string, never>,
    animatedBuildOptionValues: {},
  };
}

describe("BuildControls enemy meta / empty-defs state (regression: idle is not loading)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("requests enemy meta when controls are missing for the slug and status is idle", async () => {
    const loadSpy = vi.fn(() => Promise.resolve());
    useAppStore.setState({
      ...emptyMetaContext("unknown_new_enemy"),
      enemyMetaStatus: "idle",
      loadAnimatedEnemyMeta: stubLoad(loadSpy),
    });
    render(<BuildControls />);
    await waitFor(() => expect(loadSpy).toHaveBeenCalledTimes(1));
  });

  it("shows waiting copy when idle with empty defs — not the loading spinner (regression)", () => {
    useAppStore.setState({
      ...emptyMetaContext("unknown_new_enemy"),
      enemyMetaStatus: "idle",
      loadAnimatedEnemyMeta: stubLoad(noopLoad),
    });
    render(<BuildControls />);
    expect(screen.getByText("Waiting for enemy metadata…")).toBeInTheDocument();
    expect(screen.queryByText("Loading build controls…")).not.toBeInTheDocument();
  });

  it("shows loading spinner only when status is loading", () => {
    useAppStore.setState({
      ...emptyMetaContext("unknown_new_enemy"),
      enemyMetaStatus: "loading",
      loadAnimatedEnemyMeta: stubLoad(noopLoad),
    });
    render(<BuildControls />);
    expect(screen.getByText("Loading build controls…")).toBeInTheDocument();
    expect(screen.queryByText("Waiting for enemy metadata…")).not.toBeInTheDocument();
  });

  it("disables Retry only while loading", () => {
    useAppStore.setState({
      ...emptyMetaContext("unknown_new_enemy"),
      enemyMetaStatus: "loading",
      loadAnimatedEnemyMeta: stubLoad(noopLoad),
    });
    const { rerender } = render(<BuildControls />);
    const btn = screen.getByRole("button", { name: "Retry" });
    expect(btn).toBeDisabled();

    useAppStore.setState({ enemyMetaStatus: "idle" });
    rerender(<BuildControls />);
    expect(screen.getByRole("button", { name: "Retry" })).not.toBeDisabled();
  });

  it("still requests meta when offline defs exist for the slug but status is idle (regression: offline defs should not suppress real fetch)", async () => {
    // REGRESSION: offline seeded controls have non-empty defs per slug (zone finish/hex),
    // but they lack controls that only come from the backend (e.g. eye_shape, pupil_enabled).
    // The fetch must happen even when defs.length > 0 — only enemyMetaStatus guards re-fetches.
    const loadSpy = vi.fn(() => Promise.resolve());
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: { spider: {} },
      enemyMetaStatus: "idle",
      loadAnimatedEnemyMeta: stubLoad(loadSpy),
    });
    render(<BuildControls />);
    await waitFor(() => expect(loadSpy).toHaveBeenCalledTimes(1));
  });

  it("shows fetch error message when status is error", () => {
    useAppStore.setState({
      ...emptyMetaContext("unknown_new_enemy"),
      enemyMetaStatus: "error",
      enemyMetaError: "Network down",
      loadAnimatedEnemyMeta: stubLoad(noopLoad),
    });
    render(<BuildControls />);
    expect(screen.getByText(/Network down/)).toBeInTheDocument();
    expect(screen.queryByText("Loading build controls…")).not.toBeInTheDocument();
    expect(screen.queryByText("Waiting for enemy metadata…")).not.toBeInTheDocument();
  });

  it("body_type select_str calls setAnimatedBuildOption with no_leg_biped", () => {
    const setSpy = vi.fn();
    const bodyTypeDef: AnimatedBuildControlDef = {
      key: "body_type",
      label: "Body Type",
      type: "select_str",
      options: ["default", "standard_biped", "no_leg_biped"],
      default: "default",
    };
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "imp" },
      animatedEnemyMeta: [{ slug: "imp", label: "Imp" }],
      animatedBuildControls: { imp: [bodyTypeDef] },
      animatedBuildOptionValues: { imp: { body_type: "default" } },
      enemyMetaStatus: "ok",
      setAnimatedBuildOption: setSpy,
    });
    render(<BuildControls />);
    fireEvent.change(screen.getByDisplayValue("default"), {
      target: { value: "no_leg_biped" },
    });
    expect(setSpy).toHaveBeenCalledWith("imp", "body_type", "no_leg_biped");
  });
});
