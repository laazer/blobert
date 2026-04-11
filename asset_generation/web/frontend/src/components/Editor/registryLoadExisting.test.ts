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

  it("filterLoadExistingCandidates: empty enemyFamily string skips family filter (same as null)", () => {
    // CHECKPOINT: UI passes null when no family selected; empty string must not over-filter.
    expect(filterLoadExistingCandidates(sampleRows, "enemy", "")).toHaveLength(1);
    expect(filterLoadExistingCandidates(sampleRows, "enemy", null)).toEqual(
      filterLoadExistingCandidates(sampleRows, "enemy", ""),
    );
  });

  it("filterLoadExistingCandidates: stress ordering preserved for stable sort inputs", () => {
    const many: LoadExistingCandidate[] = Array.from({ length: 40 }, (_, i) => ({
      kind: "enemy" as const,
      family: "zoo",
      version_id: `zoo_animated_${String(i).padStart(2, "0")}`,
      path: `animated_exports/zoo_animated_${String(i).padStart(2, "0")}.glb`,
    }));
    const filtered = filterLoadExistingCandidates(many, "enemy", "zoo");
    expect(filtered).toHaveLength(40);
    expect(filtered[0]?.version_id).toBe("zoo_animated_00");
    expect(filtered[39]?.version_id).toBe("zoo_animated_39");
  });

  it("toOpenExistingRequest rejects path injection in data shape (identity-only contract)", () => {
    const rowWithExtra = {
      ...sampleRows[0],
      path: "../animated_exports/evil.glb",
    } as LoadExistingCandidate;
    const req = toOpenExistingRequest(rowWithExtra);
    expect(req).not.toHaveProperty("path");
    expect(req).toEqual({
      kind: "enemy",
      family: "imp",
      version_id: "imp_animated_00",
    });
  });
});
