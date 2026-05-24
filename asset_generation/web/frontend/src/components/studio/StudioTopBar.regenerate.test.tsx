// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import * as client from "../../api/client";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return { ...actual, fetchModelRegistry: vi.fn() };
});

import { useAppStore } from "../../store/useAppStore";
import type { ModelRegistryPayload } from "../../types";
import { StudioTopBar } from "./StudioTopBar";

const startSpy = vi.fn();

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_animated_02",
          path: "animated_exports/spider_animated_02.glb",
          draft: false,
          in_use: true,
          name: "Ember Scout",
          tags: ["spider", "fire"],
        },
      ],
    },
  },
  player: null,
  player_active_visual: null,
};

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
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
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

  it("shows version name and tags in breadcrumb when registry matches preview", async () => {
    render(<StudioTopBar />);
    expect(await screen.findByTestId("studio-top-bar-version-label")).toHaveTextContent("Ember Scout");
    expect(screen.getByTestId("studio-top-bar-tag-fire")).toBeInTheDocument();
    expect(screen.queryByTestId("studio-top-bar-tag-spider")).toBeNull();
    expect(screen.queryByRole("button", { name: /Search/i })).toBeNull();
    expect(screen.queryByRole("button", { name: "Save" })).toBeNull();
  });

  it("Generate new omits replaceVariantIndex", () => {
    render(<StudioTopBar />);
    fireEvent.click(screen.getByTestId("studio-top-generate-new"));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(startSpy.mock.calls[0][0].replaceVariantIndex).toBeUndefined();
  });

  it("Regenerate is disabled when preview path does not match selected enemy", () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/slug_animated_00.glb",
    });
    render(<StudioTopBar />);
    expect(screen.getByTestId("studio-top-regenerate")).toBeDisabled();
  });
});
