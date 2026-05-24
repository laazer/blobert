import { describe, expect, it } from "vitest";
import type { RegistryEnemyVersion } from "../types";
import { matchesStudioVersionFilter, versionPoolKind, versionRowElementId } from "./studioVersionUi";

describe("studioVersionUi", () => {
  it("classifies pool and draft from registry flags", () => {
    expect(versionPoolKind({ draft: true, in_use: false })).toBe("draft");
    expect(versionPoolKind({ draft: false, in_use: true })).toBe("pool");
    expect(versionPoolKind({ draft: false, in_use: false })).toBe("none");
  });

  it("resolves element from the version row tags", () => {
    const row: RegistryEnemyVersion = {
      id: "spider_animated_00",
      path: "x.glb",
      draft: false,
      in_use: true,
      tags: ["fire", "spider"],
    };
    expect(versionRowElementId("spider", row)).toBe("fire");
  });

  it("falls back to family heuristics when row has no element tag", () => {
    const row: RegistryEnemyVersion = {
      id: "acid_spitter_animated_00",
      path: "x.glb",
      draft: false,
      in_use: false,
      tags: ["acid_spitter"],
    };
    expect(versionRowElementId("acid_spitter", row)).toBe("acid");
  });

  it("filters versions by pool state", () => {
    const pool = { draft: false, in_use: true };
    const draft = { draft: true, in_use: false };
    expect(matchesStudioVersionFilter(pool, "all")).toBe(true);
    expect(matchesStudioVersionFilter(pool, "pool")).toBe(true);
    expect(matchesStudioVersionFilter(pool, "draft")).toBe(false);
    expect(matchesStudioVersionFilter(draft, "draft")).toBe(true);
    expect(matchesStudioVersionFilter(draft, "pool")).toBe(false);
  });
});
