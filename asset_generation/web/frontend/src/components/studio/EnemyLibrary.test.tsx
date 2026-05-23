// @vitest-environment jsdom
/**
 * STUDIO-02 — Enemy library rail wired to model registry.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ModelRegistryPayload } from "../../types";
import { REGISTRY_ENEMY_FAMILY_LS } from "../../utils/registryFamilyNav";
import { EnemyLibrary } from "./EnemyLibrary";
import { useAppStore } from "../../store/useAppStore";

const registryFixture: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_animated_05",
          path: "animated_exports/spider_animated_05.glb",
          draft: false,
          in_use: true,
          tags: ["spider", "fire"],
        },
      ],
    },
    acid_spitter: {
      versions: [
        {
          id: "acid_spitter_00",
          path: "animated_exports/acid_spitter_00.glb",
          draft: true,
          in_use: false,
          tags: ["acid_spitter", "acid"],
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
  };
});

import { fetchModelRegistry } from "../../api/client";

describe("EnemyLibrary", () => {
  afterEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
    cleanup();
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
    });
  });

  beforeEach(() => {
    vi.mocked(fetchModelRegistry).mockResolvedValue(registryFixture);
  });

  it("lists registry families on Enemies segment", async () => {
    render(<EnemyLibrary />);

    await waitFor(() => {
      expect(screen.getByTestId("studio-family-row-spider")).toBeInTheDocument();
    });
    expect(screen.getByTestId("studio-family-row-acid_spitter")).toBeInTheDocument();
    expect(screen.getByText(/2 families · 2 variants/)).toBeInTheDocument();
  });

  it("selecting a family updates command context and localStorage", async () => {
    render(<EnemyLibrary />);

    await waitFor(() => {
      expect(screen.getByTestId("studio-family-row-acid_spitter")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("studio-family-row-acid_spitter"));

    expect(useAppStore.getState().commandContext).toEqual({
      cmd: "animated",
      enemy: "acid_spitter",
    });
    expect(localStorage.getItem(REGISTRY_ENEMY_FAMILY_LS)).toBe("acid_spitter");
    expect(screen.getByTestId("studio-family-row-acid_spitter")).toHaveAttribute(
      "aria-current",
      "true",
    );
  });

  it("Player segment shows placeholder instead of family list", async () => {
    render(<EnemyLibrary />);

    await waitFor(() => {
      expect(screen.getByTestId("studio-family-row-spider")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("studio-library-segment-player"));

    expect(screen.queryByTestId("studio-family-row-spider")).not.toBeInTheDocument();
    expect(screen.getByText(/Player variants/)).toBeInTheDocument();
  });
});
