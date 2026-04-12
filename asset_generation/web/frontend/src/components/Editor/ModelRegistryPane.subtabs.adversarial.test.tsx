// @vitest-environment jsdom
/**
 * Adversarial / edge coverage for registry RunCmd sub-tabs (ticket 18).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { PLAYER_MODEL_SECTION_HEADING } from "./RegistryPlayerSection";
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

describe("ModelRegistryPane registry sub-tabs (adversarial)", () => {
  afterEach(() => {
    localStorage.removeItem("blobert.registry.subtab");
    cleanup();
  });

  beforeEach(() => {
    localStorage.setItem("blobert.registry.subtab", "not-a-valid-cmd");
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

  it("falls back to Animated when localStorage holds an unknown cmd token", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Enemy version slots & versions" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: PLAYER_MODEL_SECTION_HEADING })).not.toBeInTheDocument();
  });

  it("does not refetch registry when switching to Level tab (empty state only)", async () => {
    const fetchRegistry = vi.mocked(client.fetchModelRegistry);
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Level" })).toBeInTheDocument();
    });
    const callsAfterLoad = fetchRegistry.mock.calls.length;
    expect(callsAfterLoad).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("tab", { name: "Level" }));

    await waitFor(() => {
      expect(screen.getByText(/not available in the manifest/i)).toBeInTheDocument();
    });
    expect(fetchRegistry.mock.calls.length).toBe(callsAfterLoad);
  });

  it("Stats tab shows N/A copy and does not mount enemy or player headings", async () => {
    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Stats" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Stats" }));

    await waitFor(() => {
      expect(screen.getByText(/not tied to this command/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: PLAYER_MODEL_SECTION_HEADING })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Enemy version slots & versions" })).not.toBeInTheDocument();
  });
});
