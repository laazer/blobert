// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { BuildControls } from "./BuildControls";

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

  it("does not request meta when defs already exist for the slug (idle)", () => {
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
    expect(loadSpy).not.toHaveBeenCalled();
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
});
