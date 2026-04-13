// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { ModelRegistryPane } from "./ModelRegistryPane";

function registryWithSpiderVersions(versions: RegistryEnemyVersion[]): ModelRegistryPayload {
  return {
    schema_version: 1,
    enemies: { spider: { versions } },
    player_active_visual: null,
  };
}

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    putEnemyFamilySlots: vi.fn(),
    patchRegistryEnemyVersion: vi.fn(),
    deleteRegistryEnemyVersion: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane bulk enemy version selection", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.fetchEnemyFamilySlots).mockResolvedValue({
      family: "spider",
      version_ids: [],
      resolved_paths: [],
    });
    useAppStore.setState({ activeGlbUrl: null });
  });

  it("Set selected → Draft patches each checked version", async () => {
    const v0: RegistryEnemyVersion = {
      id: "spider_animated_00",
      path: "animated_exports/spider_animated_00.glb",
      draft: false,
      in_use: true,
    };
    const v1: RegistryEnemyVersion = {
      id: "spider_animated_01",
      path: "animated_exports/spider_animated_01.glb",
      draft: false,
      in_use: true,
    };
    const registry = registryWithSpiderVersions([v0, v1]);
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registry);
    vi.mocked(client.patchRegistryEnemyVersion).mockImplementation(async (family, versionId, body) => {
      const row = registry.enemies[family]?.versions.find((v) => v.id === versionId);
      if (row) {
        if (body.draft !== undefined) row.draft = body.draft;
        if (body.in_use !== undefined) row.in_use = body.in_use;
      }
      return JSON.parse(JSON.stringify(registry)) as ModelRegistryPayload;
    });

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-enemy-select-spider-spider_animated_00")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("registry-enemy-select-spider-spider_animated_00"));
    fireEvent.click(screen.getByTestId("registry-enemy-select-spider-spider_animated_01"));
    fireEvent.click(screen.getByTestId("registry-enemy-bulk-draft-spider"));

    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledTimes(2);
    });
    expect(vi.mocked(client.patchRegistryEnemyVersion).mock.calls[0]?.[1]).toBe("spider_animated_00");
    expect(vi.mocked(client.patchRegistryEnemyVersion).mock.calls[1]?.[1]).toBe("spider_animated_01");
    expect(vi.mocked(client.patchRegistryEnemyVersion).mock.calls[0]?.[2]).toEqual({
      draft: true,
      in_use: false,
    });
  });

  it("select-all toggles every row checkbox for the family", async () => {
    const v0: RegistryEnemyVersion = {
      id: "spider_animated_00",
      path: "animated_exports/spider_animated_00.glb",
      draft: false,
      in_use: true,
    };
    const v1: RegistryEnemyVersion = {
      id: "spider_animated_01",
      path: "animated_exports/spider_animated_01.glb",
      draft: false,
      in_use: true,
    };
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryWithSpiderVersions([v0, v1]));

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-enemy-select-all-spider")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("registry-enemy-select-all-spider"));
    expect((screen.getByTestId("registry-enemy-select-spider-spider_animated_00") as HTMLInputElement).checked).toBe(
      true,
    );
    expect((screen.getByTestId("registry-enemy-select-spider-spider_animated_01") as HTMLInputElement).checked).toBe(
      true,
    );
  });
});
