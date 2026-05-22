// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { REGISTRY_ENEMY_FAMILY_LS } from "../../utils/registryFamilyNav";
import { REGISTRY_TAG_FILTER_LS, REGISTRY_TAG_GROUP_LS } from "../../utils/registryTags";
import { ENEMY_VERSIONS_HELP_PARAGRAPHS } from "./registryPaneStrings";
import { ModelRegistryPane } from "./ModelRegistryPane";

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        { id: "spider_00", path: "animated_exports/spider_00.glb", draft: false, in_use: true },
      ],
    },
    acid_spitter: {
      versions: [
        {
          id: "acid_spitter_animated_00",
          path: "animated_exports/acid_spitter_animated_00.glb",
          draft: false,
          in_use: true,
        },
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

describe("ModelRegistryPane enemy family tabs", () => {
  afterEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
    localStorage.removeItem(REGISTRY_TAG_FILTER_LS);
    localStorage.removeItem(REGISTRY_TAG_GROUP_LS);
    cleanup();
  });

  beforeEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
    localStorage.removeItem(REGISTRY_TAG_FILTER_LS);
    localStorage.removeItem(REGISTRY_TAG_GROUP_LS);
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

  it("shows one family panel at a time and switches on tab click", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Acid Spitter" })).toBeInTheDocument();
    });

    // Default command-bar enemy is spider, so the first visible panel matches that family.
    expect(screen.getByTestId("registry-enemy-family-panel-spider")).toBeInTheDocument();
    expect(screen.queryByTestId("registry-enemy-family-panel-acid_spitter")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Acid Spitter" }));

    await waitFor(() => {
      expect(screen.getByTestId("registry-enemy-family-panel-acid_spitter")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("registry-enemy-family-panel-spider")).not.toBeInTheDocument();
  });

  it("does not render long help copy until Info is opened", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-enemy-versions-info")).toBeInTheDocument();
    });

    expect(screen.queryByText(ENEMY_VERSIONS_HELP_PARAGRAPHS[0])).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("registry-enemy-versions-info"));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(ENEMY_VERSIONS_HELP_PARAGRAPHS[0])).toBeInTheDocument();
  });
});
