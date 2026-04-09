// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { ModelRegistryPane } from "./ModelRegistryPane";

function pickPlayerTestId(path: string): string {
  return `player-active-model-pick-${encodeURIComponent(path)}`;
}

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_animated_00",
          path: "animated_exports/spider_animated_00.glb",
          draft: false,
          in_use: true,
        },
      ],
    },
  },
  player_active_visual: null,
};

const assetRows = [
  {
    path: "player_exports/player_slime_blue_00.glb",
    name: "player_slime_blue_00.glb",
    dir: "player_exports",
    size: 8,
  },
];

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    fetchAssets: vi.fn(),
    patchRegistryPlayerActiveVisual: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane player active model modal", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: ["spider_animated_00"],
      resolved_paths: [],
    }));
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
    vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
    vi.mocked(client.fetchAssets).mockResolvedValue(assetRows);
    vi.mocked(client.patchRegistryPlayerActiveVisual).mockResolvedValue({
      ...registryFixture,
      player_active_visual: { path: "player_exports/player_slime_blue_00.glb", draft: false },
    });
    useAppStore.setState({
      activeGlbUrl: null,
      assets: assetRows,
    });
  });

  it("opens modal from Choose game active and PATCHes the picked player export path", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("player-active-model-open")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("player-active-model-open"));

    await waitFor(() => {
      expect(screen.getByTestId("player-active-model-modal")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(pickPlayerTestId("player_exports/player_slime_blue_00.glb")));

    await waitFor(() => {
      expect(vi.mocked(client.patchRegistryPlayerActiveVisual)).toHaveBeenCalledWith({
        path: "player_exports/player_slime_blue_00.glb",
      });
    });

    await waitFor(() => {
      expect(screen.queryByTestId("player-active-model-modal")).not.toBeInTheDocument();
    });
  });

  it("shows updated game active path in the pane after a successful pick", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("player-active-model-open")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("player-active-model-open"));

    await waitFor(() => {
      expect(screen.getByTestId("player-active-model-modal")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(pickPlayerTestId("player_exports/player_slime_blue_00.glb")));

    await waitFor(() => {
      expect(screen.getByText("player_exports/player_slime_blue_00.glb")).toBeInTheDocument();
    });
  });
});
