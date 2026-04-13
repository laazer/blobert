// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { CommandPanel } from "./CommandPanel";

const startSpy = vi.fn();

vi.mock("../Terminal/useStreamingOutput", () => ({
  useStreamingOutput: () => ({ start: startSpy }),
}));

vi.mock("./SaveModelModal", () => ({
  SaveModelModal: () => null,
}));

vi.mock("./SaveScriptModal", () => ({
  SaveScriptModal: () => null,
}));

afterEach(() => {
  cleanup();
  startSpy.mockClear();
});

describe("CommandPanel Regenerate", () => {
  beforeEach(() => {
    useAppStore.setState({
      isSaving: false,
      isRunning: false,
      isDirty: false,
      selectedFile: null,
      fileTree: [],
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_02.glb?t=1",
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: {},
      animatedBuildOptionValues: {},
      enemyMetaStatus: "ok",
      enemyMetaError: null,
      metaBackend: "ok",
      metaBackendDetail: null,
    });
  });

  it("Run does not send replace_variant_index", () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(startSpy.mock.calls[0][0].replaceVariantIndex).toBeUndefined();
  });

  it("Regenerate sends replaceVariantIndex and keeps outputDraft false for live exports", () => {
    render(<CommandPanel />);
    const regen = screen.getByRole("button", { name: "Regenerate" });
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
    render(<CommandPanel />);
    expect(screen.getByRole("button", { name: "Regenerate" })).toBeDisabled();
  });
});
