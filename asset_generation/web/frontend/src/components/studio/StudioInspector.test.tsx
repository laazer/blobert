// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import type { AnimatedBuildControlDef } from "../../types";
import { StudioInspector } from "./StudioInspector";

afterEach(() => {
  cleanup();
});

describe("StudioInspector Look tab", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: mergeBuildOptionValues(controls, {}),
      centerPanel: "code",
      commandExportFinish: "matte",
      commandExportHexColor: "",
      enemyMetaStatus: "ok",
    });
  });

  it("mounts mockup-style Look panel on Look tab", async () => {
    render(<StudioInspector />);

    expect(screen.getByTestId("studio-inspector-panel-look")).toBeVisible();
    await waitFor(() => {
      expect(screen.getByTestId("studio-look-panel")).toBeInTheDocument();
    });
    expect(screen.getByTestId("studio-look-element-grid")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-part-picker")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-background")).toBeInTheDocument();
    expect(screen.getByText("Element")).toBeInTheDocument();
  });
});

describe("StudioInspector Build tab", () => {
  const EYE_COUNT_DEF: AnimatedBuildControlDef = {
    key: "eye_count",
    label: "Count",
    type: "select",
    options: [1, 2, 3, 4],
    default: 2,
  };

  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({ spider: [EYE_COUNT_DEF] }, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: mergeBuildOptionValues(controls, {}),
      centerPanel: "code",
      enemyMetaStatus: "ok",
    });
  });

  it("mounts BuildControls on Build tab instead of placeholder copy", async () => {
    render(<StudioInspector />);

    fireEvent.click(screen.getByTestId("studio-inspector-tab-build"));

    expect(screen.getByTestId("studio-inspector-panel-build")).toBeVisible();
    await waitFor(() => {
      expect(screen.getByTestId("studio-build-controls")).toBeInTheDocument();
    });
    expect(screen.getByTestId("studio-build-controls")).toBeInTheDocument();
    expect(screen.getByTestId("studio-build-panel")).toBeInTheDocument();
    expect(screen.getByTestId("studio-build-segmented-eye_count")).toBeInTheDocument();
    expect(screen.queryByText(/BuildControls \(Phase 2\)/)).toBeNull();
  });
});

describe("StudioInspector Code tab", () => {
  beforeEach(() => {
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      commandExportFinish: "matte",
      commandExportHexColor: "",
      terminalLines: [],
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      activeGlbUrl: null,
    });
  });

  it("mounts StudioCodePanel on Code tab", () => {
    render(<StudioInspector />);
    fireEvent.click(screen.getByTestId("studio-inspector-tab-code"));
    expect(screen.getByTestId("studio-code-panel")).toBeInTheDocument();
    expect(screen.getByTestId("studio-code-command-input")).toBeInTheDocument();
    expect(screen.getByTestId("studio-code-log")).toBeInTheDocument();
    expect(screen.queryByText(/Phase 2/)).toBeNull();
  });
});
