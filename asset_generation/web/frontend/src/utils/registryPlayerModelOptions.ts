import type { ModelRegistryPayload } from "../types";

export type PlayerModelSelectOption = { path: string; label: string };

/** Paths under ``player_exports/`` from the asset index (disk), allowlisted server-side. */
export function playerExportGlbPathsFromAssets(assets: readonly { path: string }[]): string[] {
  const out: string[] = [];
  for (const a of assets) {
    if (a.path.startsWith("player_exports/") && a.path.endsWith(".glb")) {
      out.push(a.path);
    }
  }
  out.sort((x, y) => x.localeCompare(y));
  return out;
}

/**
 * Options for choosing the player active-visual path: registry enemy .glb rows, on-disk ``player_exports/``,
 * and the current registry value when missing from both.
 */
export function buildPlayerModelSelectOptions(
  data: ModelRegistryPayload | null,
  glbPathsFromEnemies: readonly { path: string }[],
  extraAllowlistedGlbs: readonly string[] = [],
): PlayerModelSelectOption[] {
  if (!data) return [];
  const seen = new Set<string>();
  const rows: PlayerModelSelectOption[] = [];
  for (const c of glbPathsFromEnemies) {
    if (!c.path || seen.has(c.path)) continue;
    seen.add(c.path);
    rows.push({ path: c.path, label: c.path });
  }
  for (const p of extraAllowlistedGlbs) {
    if (!p || seen.has(p)) continue;
    seen.add(p);
    rows.push({ path: p, label: `${p} (player_exports)` });
  }
  const active = data.player_active_visual?.path?.trim();
  if (active && !seen.has(active)) {
    rows.push({ path: active, label: `${active} (current registry)` });
  }
  rows.sort((a, b) => a.path.localeCompare(b.path));
  return rows;
}
