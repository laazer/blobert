/** Stable key for enemy registry row selection: `{family}:{versionId}`. */
export function enemyRegistryRowKey(family: string, versionId: string): string {
  return `${family}:${versionId}`;
}

export function parseEnemyRegistryRowKey(key: string): { family: string; versionId: string } | null {
  const i = key.indexOf(":");
  if (i <= 0 || i === key.length - 1) return null;
  return { family: key.slice(0, i), versionId: key.slice(i + 1) };
}

export function pruneEnemyVersionSelectionKeys(
  prev: ReadonlySet<string>,
  enemies: Record<string, { versions: { id: string }[] }>,
): Set<string> {
  const next = new Set<string>();
  for (const key of prev) {
    const parsed = parseEnemyRegistryRowKey(key);
    if (!parsed) continue;
    if (enemies[parsed.family]?.versions.some((v) => v.id === parsed.versionId)) {
      next.add(key);
    }
  }
  return next;
}
