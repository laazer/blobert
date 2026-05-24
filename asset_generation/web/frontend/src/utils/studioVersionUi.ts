import { ELEMENTS, type ElementId } from "../constants/elements";
import type { RegistryEnemyVersion } from "../types";
import { inferFamilyElementId } from "./inferFamilyElement";
import { versionTags } from "./registryTags";

const ELEMENT_IDS = Object.keys(ELEMENTS) as ElementId[];

export type StudioVersionFilter = "all" | "pool" | "draft";

export type VersionPoolKind = "pool" | "draft" | "none";

export function versionPoolKind(row: Pick<RegistryEnemyVersion, "draft" | "in_use">): VersionPoolKind {
  if (row.draft) return "draft";
  if (row.in_use) return "pool";
  return "none";
}

export function matchesStudioVersionFilter(
  row: Pick<RegistryEnemyVersion, "draft" | "in_use">,
  filter: StudioVersionFilter,
): boolean {
  if (filter === "all") return true;
  const kind = versionPoolKind(row);
  if (filter === "pool") return kind === "pool";
  return kind === "draft";
}

/** Element accent for one version row (tags on that row, then family heuristics). */
export function versionRowElementId(family: string, row: RegistryEnemyVersion): ElementId {
  for (const tag of versionTags(row, family)) {
    if (ELEMENT_IDS.includes(tag as ElementId)) {
      return tag as ElementId;
    }
  }
  return inferFamilyElementId(family, []);
}

/** @deprecated Prefer {@link versionRowElementId} for per-version UI. */
export function versionElementId(
  family: string,
  row: RegistryEnemyVersion,
  familyVersions: readonly RegistryEnemyVersion[],
): ElementId {
  return inferFamilyElementId(family, familyVersions.length > 0 ? familyVersions : [row]);
}

export function elementTagChipStyle(elementId: ElementId): {
  background: string;
  color: string;
  border: string;
} {
  const e = ELEMENTS[elementId];
  return {
    background: e.soft,
    color: e.ink,
    border: `1px solid color-mix(in srgb, ${e.hue} 35%, transparent)`,
  };
}

export function versionGlbLabel(versionId: string): string {
  return versionId.endsWith(".glb") ? versionId : `${versionId}.glb`;
}
