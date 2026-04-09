import { describe, expect, it } from "vitest";
import {
  ENEMY_EMPTY_SLOTS_COPY,
  nextEnemySlotsAfterAdd,
  nextEnemySlotsAfterRemove,
} from "./ModelRegistryPane";

describe("ModelRegistryPane enemy slot UI contracts", () => {
  it("adds only non-draft, in-use version ids not already slotted", () => {
    const candidates = [
      { id: "spider_animated_draft", draft: true, in_use: false },
      { id: "spider_animated_disabled", draft: false, in_use: false },
      { id: "spider_animated_00", draft: false, in_use: true },
    ];
    expect(nextEnemySlotsAfterAdd([], candidates)).toEqual(["spider_animated_00"]);
  });

  it("returns the same slot list when no eligible versions remain", () => {
    const candidates = [{ id: "spider_animated_00", draft: false, in_use: true }];
    const existing = ["spider_animated_00"];
    expect(nextEnemySlotsAfterAdd(existing, candidates)).toBe(existing);
  });

  it("removes slot rows by index to produce full replacement payload order", () => {
    const before = ["spider_animated_01", "spider_animated_00"];
    expect(nextEnemySlotsAfterRemove(before, 0)).toEqual(["spider_animated_00"]);
  });

  it("documents empty-slot fallback messaging for runtime safety", () => {
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("falls back");
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("legacy default path");
  });
});
