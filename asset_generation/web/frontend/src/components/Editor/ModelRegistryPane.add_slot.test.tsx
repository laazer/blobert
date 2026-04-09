// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { ModelRegistryPane } from "./ModelRegistryPane";

const baseVersions: RegistryEnemyVersion[] = [
  {
    id: "spider_animated_00",
    path: "animated_exports/spider_animated_00.glb",
    draft: false,
    in_use: true,
  },
  {
    id: "spider_animated_01",
    path: "animated_exports/spider_animated_01.glb",
    draft: false,
    in_use: true,
  },
];

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
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane Add slot", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    useAppStore.setState({ activeGlbUrl: null });
  });

  it("disables Add slot when every slottable version is already listed", async () => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryWithSpiderVersions([...baseVersions]));
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: ["spider_animated_00", "spider_animated_01"],
      resolved_paths: [],
    }));

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-add-slot-spider")).toBeInTheDocument();
    });

    expect(screen.getByTestId("registry-add-slot-spider")).toBeDisabled();
  });

  it("enables Add slot when an eligible version is not yet listed", async () => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryWithSpiderVersions([...baseVersions]));
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: ["spider_animated_00"],
      resolved_paths: [],
    }));

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-add-slot-spider")).toBeInTheDocument();
    });

    expect(screen.getByTestId("registry-add-slot-spider")).not.toBeDisabled();
  });

  it("prefers preview variant so Add slot appends the previewed version", async () => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryWithSpiderVersions([...baseVersions]));
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: ["spider_animated_00"],
      resolved_paths: [],
    }));
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_01.glb",
    });

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-add-slot-spider")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("registry-add-slot-spider"));

    await waitFor(() => {
      const slotSelects = screen
        .getAllByRole("combobox")
        .filter((el) => el.id !== "player-active-visual-select");
      expect(slotSelects).toHaveLength(2);
      expect(slotSelects[1]).toHaveValue("spider_animated_01");
    });
  });
});
