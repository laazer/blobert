// @vitest-environment jsdom
/**
 * Regression: derived registry lists must not use hooks after early returns (loading / error),
 * or React throws "Rendered more hooks than during the previous render."
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { ModelRegistryPane } from "./ModelRegistryPane";

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        { id: "spider_00", path: "animated_exports/spider_00.glb", draft: false, in_use: true },
      ],
    },
  },
  player_active_visual: { path: "player_exports/p.glb", draft: false },
};

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane hooks", () => {
  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: [],
      resolved_paths: [],
    }));
    vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
  });

  it("uses the same hook sequence after loading finishes (loading → loaded)", async () => {
    let resolveRegistry!: (value: ModelRegistryPayload) => void;
    vi.mocked(client.fetchModelRegistry).mockImplementation(
      () =>
        new Promise<ModelRegistryPayload>((resolve) => {
          resolveRegistry = resolve;
        }),
    );

    render(<ModelRegistryPane />);
    expect(screen.getByText(/Loading model registry/)).toBeTruthy();

    await waitFor(() => {
      expect(vi.mocked(client.fetchModelRegistry)).toHaveBeenCalled();
    });
    resolveRegistry(registryFixture);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Player model" })).toBeTruthy();
    });
  });
});
