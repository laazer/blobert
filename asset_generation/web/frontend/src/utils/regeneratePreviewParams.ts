import type { RunCmd } from "../types";
import { normalizeAnimatedSlug } from "./enemyDisplay";
import { parseAnimatedEnemyExportFilename, parseVariantFilename } from "./glbVariants";
import { previewPathFromAssetsUrl } from "./previewPathFromAssetsUrl";

export type RegeneratePreviewParams = {
  replaceVariantIndex: number;
  outputDraft: boolean;
};

/**
 * When the 3D preview shows an export GLB for the selected cmd/enemy, return params so a run
 * overwrites that file instead of allocating the next variant index.
 */
export function regeneratePreviewParams(
  cmd: RunCmd,
  enemy: string,
  activeGlbUrl: string | null,
): RegeneratePreviewParams | null {
  const rel = previewPathFromAssetsUrl(activeGlbUrl);
  if (!rel || !rel.endsWith(".glb")) return null;
  const outputDraft = rel.includes("/draft/");
  const base = rel.split("/").pop() ?? "";

  if (cmd === "animated") {
    if (!enemy.trim() || enemy === "all") return null;
    const fam = normalizeAnimatedSlug(enemy);
    const parsed = parseAnimatedEnemyExportFilename(base);
    if (!parsed || normalizeAnimatedSlug(parsed.slug) !== fam) return null;
    if (!rel.startsWith("animated_exports/")) return null;
    return { replaceVariantIndex: parsed.variantIndex, outputDraft };
  }

  if (cmd === "player") {
    if (!enemy.trim()) return null;
    const parsed = parseVariantFilename(base);
    if (!parsed) return null;
    const expectedBase = `player_slime_${enemy}`;
    if (parsed.base.toLowerCase() !== expectedBase.toLowerCase()) return null;
    if (!rel.startsWith("player_exports/")) return null;
    return { replaceVariantIndex: parsed.variantIndex, outputDraft };
  }

  if (cmd === "level") {
    if (!enemy.trim()) return null;
    const parsed = parseVariantFilename(base);
    if (!parsed) return null;
    if (parsed.base.toLowerCase() !== enemy.toLowerCase()) return null;
    if (!rel.startsWith("level_exports/")) return null;
    return { replaceVariantIndex: parsed.variantIndex, outputDraft };
  }

  return null;
}
