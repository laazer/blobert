// @vitest-environment jsdom
/**
 * Registry-first build-options hydration (FEAT-20260522).
 *
 * Spec: R2 — registry snapshot before sidecar; R9 — preview-only unchanged (see previewOnly test).
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

const GLB = "animated_exports/spider_animated_05.glb";

function registrySnapshot(): Record<string, unknown> {
  return {
    eye_count: 3,
    feat_body_finish: "glossy",
    feat_body_hex: "ff00aa",
  };
}

describe("build options hydration (registry-first)", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: { spider: { eye_count: 7 } },
      commandExportFinish: "matte",
      commandExportHexColor: "#112233",
      activeGlbUrl: null,
    });
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockReset();
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
      eye_count: 99,
      feat_body_finish: "metallic",
      feat_body_hex: "#aabbcc",
    });
  });

  it("explicit import uses inline registry snapshot without sidecar fetch", async () => {
    await useAppStore
      .getState()
      .hydrateBuildOptionsFromPreviewGlbPath(GLB, registrySnapshot());

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(3);
    });

    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    expect(useAppStore.getState().commandExportFinish).toBe("glossy");
    expect(useAppStore.getState().commandExportHexColor).toBe("#ff00aa");
  });

  it("selectAssetByPath with registryBuildOptions skips sidecar fetch", async () => {
    useAppStore.getState().selectAssetByPath(GLB, {
      importBuildOptions: true,
      registryBuildOptions: registrySnapshot(),
    });

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(3);
    });

    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
  });

  it("explicit import falls back to sidecar when registry snapshot absent", async () => {
    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(GLB);

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(99);
    });

    expect(client.fetchBuildOptionsSidecarForGlbPath).toHaveBeenCalledWith(GLB);
  });

  it("sidecar with nested features restores zone colors after regenerate-style import", async () => {
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
      eye_count: 3,
      features: {
        body: { finish: "glossy", hex: "b83228", color_image: { mode: "single" } },
        head: { finish: "matte", hex: "e85d2a" },
      },
    });

    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(GLB);

    await waitFor(() => {
      const row = useAppStore.getState().animatedBuildOptionValues.spider;
      expect(row?.feat_body_finish).toBe("glossy");
      expect(row?.feat_body_hex).toBe("b83228");
      expect(row?.feat_head_hex).toBe("e85d2a");
    });
    expect(useAppStore.getState().commandExportFinish).toBe("glossy");
    expect(useAppStore.getState().commandExportHexColor).toBe("#b83228");
  });

  it("sidecar with nested zone_geometry_extras restores build and extra controls", async () => {
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
      eye_count: 4,
      zone_geometry_extras: {
        body: { kind: "bulbs", bulb_count: 6, finish: "glossy", hex: "112233" },
      },
    });

    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(GLB);

    await waitFor(() => {
      const row = useAppStore.getState().animatedBuildOptionValues.spider;
      expect(row?.eye_count).toBe(4);
      expect(row?.extra_zone_body_kind).toBe("bulbs");
      expect(row?.extra_zone_body_bulb_count).toBe(6);
      expect(row?.extra_zone_body_finish).toBe("glossy");
      expect(row?.extra_zone_body_hex).toBe("112233");
    });
  });
});
