import { normalizeAnimatedSlug, titleCaseSnake } from "./enemyDisplay";

export const REGISTRY_ENEMY_FAMILY_LS = "blobert.registry.enemyFamily";

/** Builder / command-bar slug → registry manifest family keys (first match wins). */
const COMMAND_SLUG_REGISTRY_ALIASES: Readonly<Record<string, readonly string[]>> = {
  spitter: ["acid_spitter"],
  imp: ["ember_imp"],
  slug: ["tar_slug"],
};

export function parseSavedRegistryFamily(families: readonly string[]): string | null {
  if (typeof localStorage === "undefined" || families.length === 0) return null;
  try {
    const raw = localStorage.getItem(REGISTRY_ENEMY_FAMILY_LS)?.trim();
    if (!raw) return null;
    return families.includes(raw) ? raw : null;
  } catch {
    return null;
  }
}

export function resolveRegistryFamilyFromCommandEnemy(
  commandEnemy: string,
  families: readonly string[],
): string | null {
  const slug = normalizeAnimatedSlug(commandEnemy);
  if (!slug) return null;
  if (families.includes(slug)) return slug;
  for (const candidate of COMMAND_SLUG_REGISTRY_ALIASES[slug] ?? []) {
    if (families.includes(candidate)) return candidate;
  }
  return null;
}

/**
 * Choose which registry family tab to show: keep current when valid, else saved LS,
 * else command-bar mapping, else first sorted family.
 */
export function pickRegistryEnemyFamily(
  families: readonly string[],
  current: string | null,
  commandEnemy: string | undefined,
): string | null {
  if (families.length === 0) return null;
  if (current && families.includes(current)) return current;
  const saved = parseSavedRegistryFamily(families);
  if (saved) return saved;
  if (commandEnemy) {
    const fromCmd = resolveRegistryFamilyFromCommandEnemy(commandEnemy, families);
    if (fromCmd) return fromCmd;
  }
  return families[0] ?? null;
}

export function registryFamilyTabLabel(family: string): string {
  return titleCaseSnake(family);
}
