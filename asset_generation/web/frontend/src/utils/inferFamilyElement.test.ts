import { describe, it, expect } from "vitest";
import { inferFamilyElementId } from "./inferFamilyElement";
import type { RegistryEnemyVersion } from "../types";

describe("inferFamilyElementId", () => {
  it("uses element tag on a version when present", () => {
    const versions: RegistryEnemyVersion[] = [
      { id: "a", path: "x.glb", draft: false, in_use: true, tags: ["spider", "fire"] },
    ];
    expect(inferFamilyElementId("spider", versions)).toBe("fire");
  });

  it("falls back to slug heuristic then physical", () => {
    expect(inferFamilyElementId("acid_spitter", [])).toBe("acid");
    expect(inferFamilyElementId("unknown_creature", [])).toBe("physical");
  });
});
