import type { ModelRegistryPayload } from "../types";

export type PlayerModelSelectOption = { path: string; label: string };

/**
 * Options for the player active-visual dropdown. Includes paths from in-use enemy .glb rows plus the
 * current registry value when it is not already listed (e.g. `player_exports/…` never appears under enemies).
 */
export function buildPlayerModelSelectOptions(
  data: ModelRegistryPayload | null,
  glbPathsFromEnemies: readonly { path: string }[],
): PlayerModelSelectOption[] {
  if (!data) return [];
  const seen = new Set<string>();
  const rows: PlayerModelSelectOption[] = [];
  for (const c of glbPathsFromEnemies) {
    if (!c.path || seen.has(c.path)) continue;
    seen.add(c.path);
    rows.push({ path: c.path, label: c.path });
  }
  const active = data.player_active_visual?.path?.trim();
  if (active && !seen.has(active)) {
    rows.push({ path: active, label: `${active} (current registry)` });
  }
  rows.sort((a, b) => a.path.localeCompare(b.path));
  return rows;
}
