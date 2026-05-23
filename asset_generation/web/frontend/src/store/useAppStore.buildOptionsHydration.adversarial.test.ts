// @vitest-environment jsdom
/**
 * Adversarial registry-first hydration: player parity, dual-miss, stale sidecar ignored.
 *
 * Spec: R2, R6, R9 — traceability FEAT-20260522 registry build-options snapshot.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import * as client from "../api/client";
import { useAppStore } from "./useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../utils/animatedZoneControlsMerge";
import { PLAYER_PROCEDURAL_BUILD_SLUG } from "../utils/enemyDisplay";

vi.mock("../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../api/client")>();
  return {
    ...mod,
    fetchBuildOptionsSidecarForGlbPath: vi.fn(),
  };
});

const PLAYER_GLB = "player_exports/player_slime_blue_00.glb";
const ENEMY_GLB = "animated_exports/spider_animated_05.glb";

describe("build options hydration adversarial", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs(
      {},
      ["spider", PLAYER_PROCEDURAL_BUILD_SLUG],
    );
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: {
        spider: { eye_count: 1 },
        [PLAYER_PROCEDURAL_BUILD_SLUG]: { eye_count: 2 },
      },
      commandExportFinish: "matte",
      commandExportHexColor: "#000000",
      activeGlbUrl: null,
    });
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockReset();
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue(null);
  });

  it("player explicit import uses registry snapshot without sidecar fetch", async () => {
    const before = useAppStore.getState().animatedBuildOptionValues[PLAYER_PROCEDURAL_BUILD_SLUG]?.eye_count;
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({ eye_count: 88 });

    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(PLAYER_GLB, {
      eye_count: 5,
      feat_body_finish: "glossy",
      feat_body_hex: "aabbcc",
    });

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues[PLAYER_PROCEDURAL_BUILD_SLUG]?.eye_count).toBe(5);
    });
    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    expect(before).toBe(2);
  });

  it("explicit import with neither registry nor sidecar leaves store unchanged", async () => {
    const beforeSpider = useAppStore.getState().animatedBuildOptionValues.spider?.eye_count;
    const beforeFinish = useAppStore.getState().commandExportFinish;

    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(ENEMY_GLB);
    await new Promise((r) => setTimeout(r, 50));

    expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(beforeSpider);
    expect(useAppStore.getState().commandExportFinish).toBe(beforeFinish);
    expect(client.fetchBuildOptionsSidecarForGlbPath).toHaveBeenCalledWith(ENEMY_GLB);
  });

  it("registry snapshot wins over sidecar when both would be available", async () => {
    vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({ eye_count: 77 });

    await useAppStore.getState().hydrateBuildOptionsFromPreviewGlbPath(ENEMY_GLB, { eye_count: 6 });

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(6);
    });
    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
  });

  it("selectAssetByPath passes registryBuildOptions and skips sidecar", async () => {
    useAppStore.getState().selectAssetByPath(ENEMY_GLB, {
      importBuildOptions: true,
      registryBuildOptions: { eye_count: 9, feat_body_finish: "matte", feat_body_hex: "112233" },
    });

    await waitFor(() => {
      expect(useAppStore.getState().animatedBuildOptionValues.spider?.eye_count).toBe(9);
    });
    expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
  });
});
