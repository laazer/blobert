import { describe, it, expect } from "vitest";
import {
  enemyRegistryRowKey,
  parseEnemyRegistryRowKey,
  pruneEnemyVersionSelectionKeys,
} from "./registryVersionSelection";

describe("registryVersionSelection", () => {
  it("round-trips family and version id", () => {
    const k = enemyRegistryRowKey("spider", "spider_animated_00");
    expect(parseEnemyRegistryRowKey(k)).toEqual({ family: "spider", versionId: "spider_animated_00" });
  });

  it("prunes keys when version or family is gone", () => {
    const prev = new Set([
      enemyRegistryRowKey("spider", "spider_animated_00"),
      enemyRegistryRowKey("spider", "gone"),
    ]);
    const enemies = { spider: { versions: [{ id: "spider_animated_00" }] } };
    expect([...pruneEnemyVersionSelectionKeys(prev, enemies)]).toEqual([enemyRegistryRowKey("spider", "spider_animated_00")]);
  });
});
