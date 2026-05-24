import type { ElementId } from "../constants/elements";
import { PLAYER_COLORS } from "../components/CommandPanel/commandLogic";
import type { RegistryEnemyVersion } from "../types";
import { playerColorFromPlayerSlimeExportRelativePath } from "./glbBuildOptionsHydration";

export const REGISTRY_PLAYER_COLOR_LS = "blobert.registry.playerColor";

const PLAYER_COLOR_ELEMENT: Record<string, ElementId> = {
  blue: "water",
  green: "forest",
  pink: "poison",
  purple: "poison",
  yellow: "lightning",
  orange: "fire",
  red: "fire",
  white: "physical",
};

export function playerColorLabel(color: string): string {
  const c = color.trim().toLowerCase();
  return c.charAt(0).toUpperCase() + c.slice(1);
}

export function playerColorElementId(color: string): ElementId {
  const c = color.trim().toLowerCase();
  return PLAYER_COLOR_ELEMENT[c] ?? "physical";
}

/** ``player_slime_blue_00`` → ``blue``. */
export function playerColorFromVersionId(versionId: string): string | null {
  const m = versionId.trim().match(/^player_slime_([a-z]+)_\d{2}$/i);
  return m ? m[1].toLowerCase() : null;
}

export function versionMatchesPlayerColor(
  version: Pick<RegistryEnemyVersion, "id" | "path">,
  color: string,
): boolean {
  const want = color.trim().toLowerCase();
  const fromId = playerColorFromVersionId(version.id);
  if (fromId) return fromId === want;
  const fromPath = playerColorFromPlayerSlimeExportRelativePath(version.path);
  return fromPath === want;
}

export function filterVersionsByPlayerColor(
  versions: readonly RegistryEnemyVersion[],
  color: string,
): RegistryEnemyVersion[] {
  return versions.filter((v) => versionMatchesPlayerColor(v, color));
}

export function countPlayerVersionsByColor(
  versions: readonly RegistryEnemyVersion[],
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const c of PLAYER_COLORS) counts[c] = 0;
  for (const v of versions) {
    const c = playerColorFromVersionId(v.id) ?? playerColorFromPlayerSlimeExportRelativePath(v.path);
    if (c && c in counts) counts[c] += 1;
  }
  return counts;
}

export function pickRegistryPlayerColor(
  colors: readonly string[],
  current: string | null | undefined,
  commandColor: string | undefined,
): string | null {
  if (colors.length === 0) return null;
  const cmd = commandColor?.trim().toLowerCase();
  if (cmd && colors.includes(cmd)) return cmd;
  const saved =
    typeof localStorage !== "undefined"
      ? localStorage.getItem(REGISTRY_PLAYER_COLOR_LS)?.trim().toLowerCase()
      : null;
  if (saved && colors.includes(saved)) return saved;
  if (current && colors.includes(current)) return current;
  return colors[0];
}
