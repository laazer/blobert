import type { ModelRegistryPayload, RegistryEnemyVersion } from "../types";
import { titleCaseSnake } from "./enemyDisplay";

export const REGISTRY_TAG_FILTER_LS = "blobert.registry.tagFilter";
export const REGISTRY_TAG_GROUP_LS = "blobert.registry.tagGroup";

export const SUGGESTED_REGISTRY_TAGS = ["combat", "wip", "sandbox", "deprecated", "boss", "test"] as const;

export function normalizeTagInput(raw: string): string | null {
  const s = raw.trim().toLowerCase().replace(/\s+/g, "_");
  if (!s || s.length > 48) return null;
  if (!/^[a-z0-9][a-z0-9_-]*$/.test(s)) return null;
  return s;
}

export function versionTags(row: RegistryEnemyVersion, family: string): string[] {
  if (row.tags && row.tags.length > 0) return row.tags;
  return [family];
}

export function displayVersionTags(
  row: RegistryEnemyVersion,
  family: string,
  hideTags: ReadonlySet<string>,
): string[] {
  return versionTags(row, family).filter((t) => !hideTags.has(t));
}

export function collectRegistryTagCatalog(
  data: ModelRegistryPayload,
  extraFamilies: readonly string[] = [],
): string[] {
  const seen = new Set<string>();
  const add = (t: string) => {
    if (t) seen.add(t);
  };
  for (const family of Object.keys(data.enemies)) {
    add(family);
    for (const row of data.enemies[family]?.versions ?? []) {
      for (const t of versionTags(row, family)) add(t);
    }
  }
  for (const row of data.player?.versions ?? []) {
    for (const t of versionTags(row, "player")) add(t);
  }
  for (const t of extraFamilies) add(t);
  for (const t of SUGGESTED_REGISTRY_TAGS) add(t);
  return [...seen].sort((a, b) => a.localeCompare(b));
}

export function familyMatchesTagFilter(
  family: string,
  versions: readonly RegistryEnemyVersion[],
  filterTags: readonly string[],
): boolean {
  if (filterTags.length === 0) return true;
  return filterTags.some((tag) => versions.some((row) => versionTags(row, family).includes(tag)));
}

export function filterFamiliesByTags(
  families: readonly string[],
  enemies: ModelRegistryPayload["enemies"],
  filterTags: readonly string[],
): string[] {
  if (filterTags.length === 0) return [...families];
  return families.filter((family) =>
    familyMatchesTagFilter(family, enemies[family]?.versions ?? [], filterTags),
  );
}

export type FamilyTagGroup = {
  tag: string;
  label: string;
  families: string[];
};

export function groupFamiliesByTag(
  families: readonly string[],
  enemies: ModelRegistryPayload["enemies"],
  groupTag: string,
): FamilyTagGroup[] {
  const groups = new Map<string, string[]>();
  for (const family of families) {
    const vers = enemies[family]?.versions ?? [];
    if (!vers.some((row) => versionTags(row, family).includes(groupTag))) continue;
    const cur = groups.get(groupTag) ?? [];
    cur.push(family);
    groups.set(groupTag, cur);
  }
  const fams = groups.get(groupTag) ?? [];
  if (fams.length === 0) return [];
  return [
    {
      tag: groupTag,
      label: titleCaseSnake(groupTag),
      families: [...fams].sort((a, b) => a.localeCompare(b)),
    },
  ];
}

export function parseSavedTagFilter(): string[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(REGISTRY_TAG_FILTER_LS);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((t): t is string => typeof t === "string");
  } catch {
    return [];
  }
}

export function parseSavedTagGroup(): string | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(REGISTRY_TAG_GROUP_LS)?.trim();
    return raw || null;
  } catch {
    return null;
  }
}
