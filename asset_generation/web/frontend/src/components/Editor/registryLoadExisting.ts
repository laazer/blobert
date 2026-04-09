import type { LoadExistingCandidate, OpenExistingRegistryModelRequest } from "../../api/client";

export function loadExistingCandidateKey(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `enemy:${row.family}:${row.version_id}`;
  }
  return `player:${row.path}`;
}

export function loadExistingCandidateLabel(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `${row.family}/${row.version_id} (${row.path})`;
  }
  return `player_active_visual (${row.path})`;
}

export function toOpenExistingRequest(row: LoadExistingCandidate): OpenExistingRegistryModelRequest {
  if (row.kind === "enemy") {
    return { kind: "enemy", family: row.family, version_id: row.version_id };
  }
  return { kind: "path", path: row.path };
}
