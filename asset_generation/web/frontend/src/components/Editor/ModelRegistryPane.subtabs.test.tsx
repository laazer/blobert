// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { PLAYER_POWER_TYPES_HEADING } from "./RegistryPlayerPowerTypesSection";
import { REGISTRY_ENEMY_LOAD_EXISTING_HEADING } from "./RegistryEnemyLoadExistingSection";
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
  player: { versions: [], slots: [] },
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

describe("ModelRegistryPane registry sub-tabs", () => {
  afterEach(() => {
    cleanup();
  });

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
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
  });

  it("defaults to Enemies tab with enemy section and without player section", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Enemy version slots & versions" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: PLAYER_POWER_TYPES_HEADING })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: REGISTRY_ENEMY_LOAD_EXISTING_HEADING })).toBeInTheDocument();
  });

  it("Enemies tab is labeled 'Enemies' not 'Animated'", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Enemies" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("tab", { name: "Animated" })).not.toBeInTheDocument();
  });

  it("Player tab shows player power types section and hides enemy section", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Player" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Player" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: PLAYER_POWER_TYPES_HEADING })).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: "Enemy version slots & versions" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: REGISTRY_ENEMY_LOAD_EXISTING_HEADING })).not.toBeInTheDocument();
  });

  it("Smart, Stats, and Test tabs are not rendered", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Enemies" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("tab", { name: "Smart" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Stats" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Test" })).not.toBeInTheDocument();
  });
});
