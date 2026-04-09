import { describe, expect, it } from "vitest";
import type { ModelRegistryPayload } from "../types";
import { buildPlayerModelSelectOptions, playerExportGlbPathsFromAssets } from "./registryPlayerModelOptions";

const baseRegistry = (over: Partial<ModelRegistryPayload> = {}): ModelRegistryPayload => ({
  schema_version: 1,
  enemies: {
    spider: {
      versions: [{ id: "v1", path: "animated_exports/spider_00.glb", draft: false, in_use: true }],
    },
  },
  player_active_visual: { path: "player_exports/blob_blue.glb", draft: false },
  ...over,
});

describe("buildPlayerModelSelectOptions", () => {
  it("adds current registry path when missing from enemy-derived glb list", () => {
    const data = baseRegistry();
    const opts = buildPlayerModelSelectOptions(data, [{ path: "animated_exports/spider_00.glb" }]);
    expect(opts.map((o) => o.path)).toContain("player_exports/blob_blue.glb");
    const cur = opts.find((o) => o.path === "player_exports/blob_blue.glb");
    expect(cur?.label).toContain("current registry");
  });

  it("does not duplicate when active path already appears in enemy list", () => {
    const data = baseRegistry({ player_active_visual: { path: "animated_exports/spider_00.glb", draft: false } });
    const opts = buildPlayerModelSelectOptions(data, [{ path: "animated_exports/spider_00.glb" }]);
    expect(opts.filter((o) => o.path === "animated_exports/spider_00.glb")).toHaveLength(1);
  });

  it("merges player_exports paths from the asset index", () => {
    const data = baseRegistry({ player_active_visual: null });
    const assets = [{ path: "player_exports/player_slime_red_00.glb", name: "x", dir: "player_exports", size: 1 }];
    expect(playerExportGlbPathsFromAssets(assets)).toEqual(["player_exports/player_slime_red_00.glb"]);
    const opts = buildPlayerModelSelectOptions(data, [], ["player_exports/player_slime_red_00.glb"]);
    expect(opts.map((o) => o.path)).toContain("player_exports/player_slime_red_00.glb");
  });
});
