import { describe, expect, it } from "vitest";
import {
  appendSlotIfMissing,
  canAddEnemySlot,
  nextEnemySlotsAfterAdd,
  replaceSlotAssignment,
  slotListHasDuplicates,
} from "./registrySlotOps";

describe("replaceSlotAssignment", () => {
  it("creates first slot when empty", () => {
    expect(replaceSlotAssignment([], 0, "a")).toEqual(["a"]);
  });

  it("replaces index in range", () => {
    expect(replaceSlotAssignment(["a", "b", "c"], 1, "x")).toEqual(["a", "x", "c"]);
  });

  it("appends when index past end", () => {
    expect(replaceSlotAssignment(["a"], 3, "b")).toEqual(["a", "b"]);
  });
});

describe("canAddEnemySlot", () => {
  it("is false when every in-use version is already listed", () => {
    const candidates = [{ id: "a", draft: false, in_use: true }];
    expect(canAddEnemySlot(["a"], candidates)).toBe(false);
  });

  it("is true when an eligible version remains", () => {
    const candidates = [
      { id: "a", draft: false, in_use: true },
      { id: "b", draft: false, in_use: true },
    ];
    expect(canAddEnemySlot(["a"], candidates)).toBe(true);
  });

  it("registry-fix-versions-slots-load R3: is false when the only unslotted rows are not in pool", () => {
    const candidates = [
      { id: "a", draft: false, in_use: true },
      { id: "b", draft: false, in_use: false },
    ];
    expect(canAddEnemySlot(["a"], candidates)).toBe(false);
  });

  it("registry-fix-versions-slots-load R3: matches nextEnemySlotsAfterAdd eligibility (!draft && in_use && not slotted)", () => {
    const current = ["spider_animated_00"] as string[];
    const candidates = [
      { id: "spider_animated_00", draft: false, in_use: true },
      { id: "spider_animated_01", draft: false, in_use: true },
      { id: "spider_animated_draft", draft: true, in_use: false },
    ];
    const can = canAddEnemySlot(current, candidates);
    const longer = nextEnemySlotsAfterAdd(current, candidates);
    expect(can).toBe(longer.length > current.length);
  });
});

describe("nextEnemySlotsAfterAdd", () => {
  it("uses preferred id first when provided and eligible", () => {
    const candidates = [
      { id: "a", draft: false, in_use: true },
      { id: "b", draft: false, in_use: true },
    ];
    expect(nextEnemySlotsAfterAdd(["a"], candidates, "b")).toEqual(["a", "b"]);
  });
});

describe("appendSlotIfMissing", () => {
  it("appends when absent", () => {
    expect(appendSlotIfMissing(["a"], "b")).toEqual(["a", "b"]);
  });

  it("no-op when present", () => {
    expect(appendSlotIfMissing(["a", "b"], "a")).toEqual(["a", "b"]);
  });
});

describe("slotListHasDuplicates", () => {
  it("detects duplicates", () => {
    expect(slotListHasDuplicates(["a", "a"])).toBe(true);
    expect(slotListHasDuplicates(["a", "b"])).toBe(false);
  });

  it("registry-fix-versions-slots-load R2: ignores empty slot placeholders", () => {
    expect(slotListHasDuplicates(["", ""])).toBe(false);
    expect(slotListHasDuplicates(["", "a", ""])).toBe(false);
  });
});
