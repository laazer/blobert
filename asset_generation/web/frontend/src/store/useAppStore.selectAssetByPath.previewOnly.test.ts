// @vitest-environment jsdom
/**
 * REQ-1 / AC-1.1–AC-1.3 (BUG model-load-ui-settings): preview-only selectAssetByPath must not
 * import build options or command export fields from the GLB sidecar.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import * as client from "../api/client";
import { useAppStore } from "./useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../utils/animatedZoneControlsMerge";

vi.mock("../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../api/client")>();
  return {
    ...mod,
    fetchBuildOptionsSidecarForGlbPath: vi.fn(),
  };
});

const PREVIEW_GLB = "animated_exports/spider_animated_05.glb";

describe("selectAssetByPath preview-only (REQ-1)", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: { spider: { eye_count: 7 } },
      commandExportFinish: "matte",
      commandExportHexColor: "#112233",
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_00.glb?t=0",
    });
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockReset();
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
      eye_count: 2,
      feat_body_finish: "metallic",
      feat_body_hex: "#aabbcc",
    });
  });

  it("BUG-model-load-ui-settings-preview-select-does-not-import-sidecar", async () => {
    useAppStore.getState().selectAssetByPath(PREVIEW_GLB);

    await waitFor(() => {
      expect(client.fetchBuildOptionsSidecarForGlbPath).toHaveBeenCalledWith(PREVIEW_GLB);
    });

    const state = useAppStore.getState();
    expect(state.activeGlbUrl).toMatch(/\/api\/assets\/animated_exports\/spider_animated_05\.glb\?t=\d+$/);
    expect(state.animatedBuildOptionValues.spider?.eye_count).toBe(7);
    expect(state.commandExportFinish).toBe("matte");
    expect(state.commandExportHexColor).toBe("#112233");
  });
});
