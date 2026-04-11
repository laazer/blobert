import { describe, expect, it } from "vitest";
import type { LoadExistingCandidate } from "../../api/client";
import {
  filterLoadExistingCandidates,
  loadExistingCandidateKey,
  loadExistingCandidateLabel,
  toOpenExistingRequest,
} from "./registryLoadExisting";

/** registry-fix-versions-slots-load R4 — pure helpers used by load-existing flow. */

const sampleRows: LoadExistingCandidate[] = [
  {
    kind: "enemy",
    family: "imp",
    version_id: "imp_animated_00",
    path: "animated_exports/imp_animated_00.glb",
  },
  {
    kind: "player",
    version_id: "blob_blue_00",
    path: "player_exports/blob_blue_00.glb",
  },
];

describe("registryLoadExisting", () => {
  it("toOpenExistingRequest sends identity-only payloads (no path) for enemy and player", () => {
    expect(toOpenExistingRequest(sampleRows[0])).toEqual({
      kind: "enemy",
      family: "imp",
      version_id: "imp_animated_00",
    });
    expect(toOpenExistingRequest(sampleRows[1])).toEqual({
      kind: "player",
      version_id: "blob_blue_00",
    });
  });

  it("filterLoadExistingCandidates supports type + family filters per Registry tab flow", () => {
    expect(filterLoadExistingCandidates(sampleRows, "enemy", "imp")).toHaveLength(1);
    expect(filterLoadExistingCandidates(sampleRows, "player", null)).toHaveLength(1);
    expect(filterLoadExistingCandidates(sampleRows, "all", null)).toHaveLength(2);
  });

  it("stable keys and labels for picker rows", () => {
    expect(loadExistingCandidateKey(sampleRows[0])).toBe("enemy:imp:imp_animated_00");
    expect(loadExistingCandidateKey(sampleRows[1])).toBe("player:blob_blue_00");
    expect(loadExistingCandidateLabel(sampleRows[0])).toContain("imp/imp_animated_00");
    expect(loadExistingCandidateLabel(sampleRows[1])).toContain("player/blob_blue_00");
  });
});
