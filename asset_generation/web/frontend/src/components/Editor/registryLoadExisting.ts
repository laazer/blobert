import type { LoadExistingCandidate, OpenExistingRegistryModelRequest } from "../../api/client";

export type LoadExistingTypeFilter = "all" | "player" | "enemy";

export function filterLoadExistingCandidates(
  rows: readonly LoadExistingCandidate[],
  typeFilter: LoadExistingTypeFilter,
  enemyFamily: string | null,
): LoadExistingCandidate[] {
  let out = [...rows];
  if (typeFilter === "player") {
    out = out.filter((r) => r.kind === "player");
  } else if (typeFilter === "enemy") {
    out = out.filter((r) => r.kind === "enemy");
  }
  if (enemyFamily) {
    out = out.filter((r) => r.kind !== "enemy" || r.family === enemyFamily);
  }
  return out;
}

export function loadExistingCandidateKey(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `enemy:${row.family}:${row.version_id}`;
  }
  return `player:${row.version_id}`;
}

export function loadExistingCandidateLabel(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `${row.family}/${row.version_id} (${row.path})`;
  }
  return `player/${row.version_id} (${row.path})`;
}

export function toOpenExistingRequest(row: LoadExistingCandidate): OpenExistingRegistryModelRequest {
  if (row.kind === "enemy") {
    return { kind: "enemy", family: row.family, version_id: row.version_id };
  }
  return { kind: "player", version_id: row.version_id };
}
