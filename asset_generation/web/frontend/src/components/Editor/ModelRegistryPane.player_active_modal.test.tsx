// @vitest-environment jsdom
/**
 * Player tab: power-types section renders correctly and patches player version flags.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { ModelRegistryPane } from "./ModelRegistryPane";

const playerVersion = {
  id: "player_slime_blue_00",
  path: "player_exports/player_slime_blue_00.glb",
  draft: true,
  in_use: false,
};

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
  player: {
    versions: [playerVersion],
    slots: [],
  },
  player_active_visual: null,
};

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    patchRegistryEnemyVersion: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
    postSyncDiscoveredPlayerGlbVersions: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane player tab — power types section", () => {
  afterEach(() => {
    cleanup();
    localStorage.removeItem("blobert.player.power_types");
  });

  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: [],
      resolved_paths: [],
    }));
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
    vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
    vi.mocked(client.postSyncDiscoveredPlayerGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
    vi.mocked(client.patchRegistryEnemyVersion).mockResolvedValue({
      ...registryFixture,
      player: {
        versions: [{ ...playerVersion, draft: false, in_use: true }],
        slots: [],
      },
    });
  });

  it("shows player power types section when Player tab is active", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Player" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Player" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Player power types" })).toBeInTheDocument();
    });
  });

  it("shows player version in the versions table", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Player" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Player" }));

    await waitFor(() => {
      expect(screen.getByText("player_slime_blue_00")).toBeInTheDocument();
    });
  });

  it("PATCHes player version to in_use when In pool radio is selected", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Player" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Player" }));

    await waitFor(() => {
      expect(screen.getByTestId("player-version-spawn-player_slime_blue_00-pool")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("player-version-spawn-player_slime_blue_00-pool"));

    await waitFor(() => {
      expect(vi.mocked(client.patchRegistryEnemyVersion)).toHaveBeenCalledWith(
        "player",
        "player_slime_blue_00",
        { draft: false, in_use: true },
      );
    });
  });

  it("scan player exports button triggers postSyncDiscoveredPlayerGlbVersions", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Player" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Player" }));

    await waitFor(() => {
      expect(screen.getByTestId("player-scan-exports")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("player-scan-exports"));

    await waitFor(() => {
      expect(vi.mocked(client.postSyncDiscoveredPlayerGlbVersions)).toHaveBeenCalled();
    });
  });
});
