// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { StudioTopBar } from "./StudioTopBar";

const startSpy = vi.fn();

vi.mock("../Terminal/useStreamingOutput", () => ({
  useStreamingOutput: () => ({ start: startSpy }),
}));

vi.mock("../CommandPanel/SaveScriptModal", () => ({
  SaveScriptModal: () => null,
}));

afterEach(() => {
  cleanup();
  startSpy.mockClear();
});

describe("StudioTopBar Regenerate", () => {
  beforeEach(() => {
    useAppStore.setState({
      isSaving: false,
      isRunning: false,
      isDirty: false,
      selectedFile: null,
      fileTree: [],
      commandContext: { cmd: "animated", enemy: "spider" },
      commandExportFinish: "matte",
      commandExportHexColor: "",
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_02.glb?t=1",
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: {},
      animatedBuildOptionValues: {},
    });
  });

  it("Regenerate sends replaceVariantIndex for matching preview GLB", () => {
    render(<StudioTopBar />);
    const regen = screen.getByTestId("studio-top-regenerate");
    expect(regen).not.toBeDisabled();
    fireEvent.click(regen);
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(startSpy.mock.calls[0][0]).toMatchObject({
      replaceVariantIndex: 2,
      outputDraft: false,
      cmd: "animated",
      enemy: "spider",
    });
  });

  it("Regenerate is disabled when preview path does not match selected enemy", () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/slug_animated_00.glb",
    });
    render(<StudioTopBar />);
    expect(screen.getByTestId("studio-top-regenerate")).toBeDisabled();
  });
});
