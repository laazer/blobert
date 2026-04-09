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
    patchRegistryEnemyVersion: vi.fn(),
    postSyncDiscoveredAnimatedGlbVersions: vi.fn(),
  };
});

import * as client from "../../api/client";

describe("ModelRegistryPane Add slot", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    vi.mocked(client.patchRegistryEnemyVersion).mockReset();
    vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions).mockImplementation(() =>
      vi.mocked(client.fetchModelRegistry)(),
    );
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
      expect(screen.getByTestId("add-enemy-slot-modal")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("registry-add-slot-pick-spider_animated_01"));

    await waitFor(() => {
      const slotSelects = screen.getAllByRole("combobox");
      expect(slotSelects).toHaveLength(2);
      expect(slotSelects[1]).toHaveValue("spider_animated_01");
    });
  });

  it("add slot turns on in pool when the chosen version was not in_use", async () => {
    const v0 = { ...baseVersions[0] };
    const v1 = { ...baseVersions[1], in_use: false };
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryWithSpiderVersions([v0, v1]));
    vi.mocked(client.fetchEnemyFamilySlots).mockImplementation(async (family: string) => ({
      family,
      version_ids: ["spider_animated_00"],
      resolved_paths: [],
    }));
    vi.mocked(client.patchRegistryEnemyVersion).mockResolvedValue(
      registryWithSpiderVersions([v0, { ...v1, in_use: true }]),
    );

    render(<ModelRegistryPane />);

    await waitFor(() => {
      expect(screen.getByTestId("registry-add-slot-spider")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("registry-add-slot-spider"));
    await waitFor(() => {
      expect(screen.getByTestId("add-enemy-slot-modal")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("registry-add-slot-pick-spider_animated_01"));

    await waitFor(() => {
      expect(vi.mocked(client.patchRegistryEnemyVersion)).toHaveBeenCalledWith("spider", "spider_animated_01", {
        in_use: true,
      });
    });
  });

  it("calls sync_animated_exports before opening the add-slot modal", async () => {
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

    fireEvent.click(screen.getByTestId("registry-add-slot-spider"));

    await waitFor(() => {
      expect(vi.mocked(client.postSyncDiscoveredAnimatedGlbVersions)).toHaveBeenCalledWith("spider");
    });
    await waitFor(() => {
      expect(screen.getByTestId("add-enemy-slot-modal")).toBeInTheDocument();
    });
  });
});
