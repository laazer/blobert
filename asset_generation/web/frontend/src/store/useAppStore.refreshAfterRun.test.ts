// @vitest-environment jsdom
/**
 * After regenerate (same GLB path), in-session build options must not be overwritten by sidecar import.
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
    fetchAssets: vi.fn().mockResolvedValue([]),
    fetchBuildOptionsSidecarForGlbPath: vi.fn(),
  };
});

const GLB = "animated_exports/spider_animated_02.glb";

describe("refreshAssetsAndAutoSelect", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedBuildControls: controls,
      animatedBuildOptionValues: { spider: { eye_count: 7, feat_body_finish: "matte" } },
      commandExportFinish: "glossy",
      commandExportHexColor: "#ff5500",
      activeGlbUrl: `/api/assets/${GLB}?t=100`,
    });
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockReset();
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
      eye_count: 2,
      feat_body_finish: "metallic",
    });
  });

  it("does not import sidecar when output overwrites the same preview GLB (regenerate)", async () => {
    await useAppStore.getState().refreshAssetsAndAutoSelect(GLB);

    await waitFor(() => {
      expect(useAppStore.getState().activeGlbUrl).toMatch(/spider_animated_02\.glb/);
    });

    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(7);
    expect(useAppStore.getState().commandExportFinish).toBe("glossy");
  });

  it("imports sidecar when output is a new GLB path", async () => {
    const NEW = "animated_exports/spider_animated_09.glb";
    await useAppStore.getState().refreshAssetsAndAutoSelect(NEW);

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(2);
    });

    expect(client.fetchBuildOptionsSidecarForGlbPath).toHaveBeenCalledWith(NEW);
    expect(useAppStore.getState().commandExportFinish).toBe("metallic");
  });
});
