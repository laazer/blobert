import type { ElementId } from "../constants/elements";
import { ELEMENTS } from "../constants/elements";
import type { RegistryEnemyVersion } from "../types";
import { versionTags } from "./registryTags";

const ELEMENT_IDS = Object.keys(ELEMENTS) as ElementId[];

/** Pick an element accent for a registry family from version tags or family slug heuristics. */
export function inferFamilyElementId(
  family: string,
  versions: readonly RegistryEnemyVersion[],
): ElementId {
  for (const row of versions) {
    for (const tag of versionTags(row, family)) {
      if (ELEMENT_IDS.includes(tag as ElementId)) {
        return tag as ElementId;
      }
    }
  }
  const lower = family.toLowerCase();
  for (const id of ELEMENT_IDS) {
    if (lower.includes(id)) {
      return id;
    }
  }
  return "physical";
}
