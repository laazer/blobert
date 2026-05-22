import { describe, it, expect } from "vitest";
import {
  collectRegistryTagCatalog,
  displayVersionTags,
  filterFamiliesByTags,
  normalizeTagInput,
  versionTags,
} from "./registryTags";
import type { ModelRegistryPayload } from "../types";

const payload: ModelRegistryPayload = {
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
  player_active_visual: null,
};

describe("registryTags", () => {
  it("normalizeTagInput lowercases and underscores spaces", () => {
    expect(normalizeTagInput(" Combat Ready ")).toBe("combat_ready");
  });

  it("displayVersionTags hides group and family tags", () => {
    const row = payload.enemies.spider.versions[0];
    expect(displayVersionTags(row, "spider", new Set(["spider", "combat"]))).toEqual([]);
    expect(displayVersionTags(row, "spider", new Set(["spider"]))).toEqual(["combat"]);
  });

  it("filterFamiliesByTags uses OR semantics", () => {
    const all = ["acid_spitter", "spider"];
    expect(filterFamiliesByTags(all, payload.enemies, ["combat"])).toEqual(["spider"]);
    expect(filterFamiliesByTags(all, payload.enemies, [])).toEqual(all);
  });

  it("versionTags falls back to family slug", () => {
    expect(versionTags({ id: "x", path: "animated_exports/x.glb", draft: true, in_use: false }, "imp")).toEqual([
      "imp",
    ]);
  });

  it("collectRegistryTagCatalog merges manifest and suggestions", () => {
    const catalog = collectRegistryTagCatalog(payload);
    expect(catalog).toContain("spider");
    expect(catalog).toContain("combat");
    expect(catalog).toContain("wip");
    expect(catalog).toContain("sandbox");
  });
});
