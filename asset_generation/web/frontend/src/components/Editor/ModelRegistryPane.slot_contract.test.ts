import { describe, expect, it } from "vitest";
import {
  ENEMY_EMPTY_SLOTS_COPY,
  LOAD_EXISTING_EMPTY_COPY,
  loadExistingCandidateKey,
  loadExistingCandidateLabel,
  nextEnemySlotsAfterAdd,
  nextEnemySlotsAfterRemove,
  toOpenExistingRequest,
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

  it("maps backend candidates one-to-one to stable UI keys", () => {
    expect(
      loadExistingCandidateKey({
        kind: "enemy",
        family: "alpha",
        version_id: "alpha_live_00",
        path: "animated_exports/alpha_live_00.glb",
      }),
    ).toBe("enemy:alpha:alpha_live_00");
    expect(
      loadExistingCandidateKey({
        kind: "player",
        path: "player_exports/blobert_blue_00.glb",
      }),
    ).toBe("player:player_exports/blobert_blue_00.glb");
  });

  it("builds open requests from candidate identity only (no arbitrary manual path input control)", () => {
    expect(
      toOpenExistingRequest({
        kind: "enemy",
        family: "alpha",
        version_id: "alpha_live_00",
        path: "animated_exports/alpha_live_00.glb",
      }),
    ).toEqual({
      kind: "enemy",
      family: "alpha",
      version_id: "alpha_live_00",
    });
    expect(
      toOpenExistingRequest({
        kind: "player",
        path: "player_exports/blobert_blue_00.glb",
      }),
    ).toEqual({
      kind: "path",
      path: "player_exports/blobert_blue_00.glb",
    });
  });

  it("renders clear labels and empty-state guidance for constrained picker UX", () => {
    expect(
      loadExistingCandidateLabel({
        kind: "enemy",
        family: "alpha",
        version_id: "alpha_live_00",
        path: "animated_exports/alpha_live_00.glb",
      }),
    ).toContain("alpha/alpha_live_00");
    expect(LOAD_EXISTING_EMPTY_COPY.toLowerCase()).toContain("no draft or in-use registry models available");
  });
});
