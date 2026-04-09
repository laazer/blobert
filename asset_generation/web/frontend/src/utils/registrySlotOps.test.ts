import { describe, expect, it } from "vitest";
import { appendSlotIfMissing, replaceSlotAssignment, slotListHasDuplicates } from "./registrySlotOps";

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
