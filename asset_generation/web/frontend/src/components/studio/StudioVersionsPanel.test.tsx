// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import * as client from "../../api/client";
import type { ModelRegistryPayload } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { StudioInspector } from "./StudioInspector";

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchModelRegistry: vi.fn(),
    fetchEnemyFamilySlots: vi.fn(),
    fetchLoadExistingCandidates: vi.fn(),
  };
});

const registryFixture: ModelRegistryPayload = {
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
  player: { versions: [], slots: [] },
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("StudioVersionsPanel", () => {
  beforeEach(() => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registryFixture);
    vi.mocked(client.fetchEnemyFamilySlots).mockResolvedValue({
      version_ids: ["spider_animated_00"],
      resolved_paths: ["animated_exports/spider_animated_00.glb"],
    });
    vi.mocked(client.fetchLoadExistingCandidates).mockResolvedValue({ candidates: [] });
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
      centerPanel: "code",
    });
  });

  it("renders registry controls on Versions tab instead of placeholder", async () => {
    render(<StudioInspector />);
    fireEvent.click(screen.getByTestId("studio-inspector-tab-versions"));

    expect(screen.getByTestId("studio-inspector-panel-versions")).toBeVisible();
    await waitFor(() => {
      expect(screen.getByTestId("studio-versions-panel")).toBeInTheDocument();
    });
    expect(screen.getByTestId("studio-version-list")).toBeInTheDocument();
    expect(screen.getByTestId("studio-version-filter-all")).toBeInTheDocument();
    expect(screen.getByTestId(`studio-version-row-spider_animated_00`)).toBeInTheDocument();
    expect(screen.queryByTestId("registry-subtab-animated")).toBeNull();
  });

  it("shows empty state when cmd is not animated or player", () => {
    useAppStore.setState({ commandContext: { cmd: "level", enemy: "obj1" } });
    render(<StudioInspector />);
    fireEvent.click(screen.getByTestId("studio-inspector-tab-versions"));
    expect(screen.getByTestId("studio-versions-empty")).toBeInTheDocument();
  });
});
