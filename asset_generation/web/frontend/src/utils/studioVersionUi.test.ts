import { describe, expect, it } from "vitest";
import { matchesStudioVersionFilter, versionPoolKind } from "./studioVersionUi";

describe("studioVersionUi", () => {
  it("classifies pool and draft from registry flags", () => {
    expect(versionPoolKind({ draft: true, in_use: false })).toBe("draft");
    expect(versionPoolKind({ draft: false, in_use: true })).toBe("pool");
    expect(versionPoolKind({ draft: false, in_use: false })).toBe("none");
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
