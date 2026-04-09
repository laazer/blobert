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

  it("is true when a non-draft version is not in pool but not yet slotted", () => {
    const candidates = [
      { id: "a", draft: false, in_use: true },
      { id: "b", draft: false, in_use: false },
    ];
    expect(canAddEnemySlot(["a"], candidates)).toBe(true);
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
});
