// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import * as client from "../api/client";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, fetchModelRegistry: vi.fn() };
});
import { useAppStore } from "../store/useAppStore";
import type { ModelRegistryPayload } from "../types";
import { useStudioPreviewVersion } from "./useStudioPreviewVersion";

const registry: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_animated_02",
          path: "animated_exports/spider_animated_02.glb",
          draft: false,
          in_use: true,
          name: "Fire Queen",
          tags: ["spider", "fire", "combat"],
        },
      ],
    },
  },
  player: null,
  player_active_visual: null,
};

describe("useStudioPreviewVersion", () => {
  beforeEach(() => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registry);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_02.glb?t=1",
      registryReloadSeq: 0,
    });
  });

  it("resolves version label and display tags from preview GLB", async () => {
    const { result } = renderHook(() => useStudioPreviewVersion());
    await waitFor(() => {
      expect(result.current.versionLabel).toBe("Fire Queen");
    });
    expect(result.current.breadcrumbTags).toEqual(["fire", "combat"]);
  });
});
