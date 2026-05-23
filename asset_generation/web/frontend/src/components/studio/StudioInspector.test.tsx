// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
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
