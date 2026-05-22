// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { REGISTRY_ENEMY_FAMILY_LS } from "../../utils/registryFamilyNav";
import { ModelRegistryPane } from "./ModelRegistryPane";

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_00",
          path: "animated_exports/spider_00.glb",
          draft: false,
          in_use: true,
          tags: ["spider", "combat"],
        },
      ],
    },
    acid_spitter: {
      versions: [
        {
          id: "acid_00",
          path: "animated_exports/acid_00.glb",
          draft: false,
          in_use: true,
          tags: ["acid_spitter", "wip"],
        },
      ],
    },
  },
  player: { versions: [], slots: [] },
  player_active_visual: null,
};

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
    patchRegistryEnemyVersion: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane tags", () => {
  afterEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
    cleanup();
  });

  beforeEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: [],
      resolved_paths: [],
    }));
    vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
    vi.mocked(client.patchRegistryEnemyVersion).mockResolvedValue(registryFixture);
  });

  it("shows tag organizer and hides family tag on the active family row", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-tag-organizer")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("tab", { name: "Acid Spitter" }));

    await waitFor(() => {
      expect(screen.getByTestId("registry-tag-chip-wip")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("registry-tag-chip-acid_spitter")).not.toBeInTheDocument();
  });

  it("persists a new tag via patch API", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-tag-input-spider-spider_00")).toBeInTheDocument();
    });

    const input = screen.getByTestId("registry-tag-input-spider-spider_00");
    fireEvent.change(input, { target: { value: "boss" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledWith("spider", "spider_00", {
        tags: ["spider", "combat", "boss"],
      });
    });
  });
});
