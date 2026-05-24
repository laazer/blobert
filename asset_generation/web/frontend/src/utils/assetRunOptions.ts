import type { AnimatedBuildControlDef } from "../types";
import type { RunCmd } from "../types";
import {
  CMD_CONFIG,
  ENEMY_FINISHES,
  partitionAnimatedBuildOptionsForJson,
  PLAYER_COLORS,
  PLAYER_FINISHES,
  prunePartitionedBuildOptionsForRun,
} from "../components/CommandPanel/commandLogic";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "./enemyDisplay";
import { previewPathFromAssetsUrl } from "./previewPathFromAssetsUrl";
import { regeneratePreviewParams } from "./regeneratePreviewParams";

export type AssetRunFieldState = {
  cmd: RunCmd;
  enemy: string;
  description: string;
  difficulty: string;
  finish: string;
  hexColor: string;
  commandPreviewDirty: boolean;
};

export type AssetRunOptions = {
  cmd: RunCmd;
  enemy?: string;
  count?: number;
  description?: string;
  difficulty?: string;
  finish?: string;
  hexColor?: string;
  buildOptionsJson?: string;
  outputDraft?: boolean;
  replaceVariantIndex?: number;
};

export function validateAssetRun(
  fields: AssetRunFieldState,
  activeGlbUrl: string | null,
): string | null {
  if (fields.commandPreviewDirty) return "Apply command preview changes before running.";
  const cfg = CMD_CONFIG[fields.cmd];
  if (cfg.showEnemy && cfg.requiresEnemy && !fields.enemy.trim()) {
    return "Enemy is required for this cmd.";
  }
  if (fields.cmd === "player" && !PLAYER_COLORS.includes(fields.enemy)) {
    return `Player cmd requires a slime color (${PLAYER_COLORS.join(", ")}).`;
  }
  if (fields.cmd === "player" && !PLAYER_FINISHES.includes(fields.finish)) {
    return `Player finish must be one of: ${PLAYER_FINISHES.join(", ")}.`;
  }
  if (fields.cmd === "animated" && !ENEMY_FINISHES.includes(fields.finish)) {
    return `Enemy finish must be one of: ${ENEMY_FINISHES.join(", ")}.`;
  }
  if (fields.cmd === "player" && fields.hexColor && !/^#[0-9a-fA-F]{6}$/.test(fields.hexColor)) {
    return "Custom color must be in #RRGGBB format.";
  }
  if (fields.cmd === "animated" && fields.hexColor && !/^#[0-9a-fA-F]{6}$/.test(fields.hexColor)) {
    return "Custom color must be in #RRGGBB format.";
  }
  if (activeGlbUrl == null) return null;
  return null;
}

export function canRegenerateAsset(
  fields: Pick<AssetRunFieldState, "cmd" | "enemy">,
  activeGlbUrl: string | null,
  runValidationError: string | null,
): boolean {
  if (runValidationError) return false;
  if (fields.cmd !== "animated" && fields.cmd !== "player" && fields.cmd !== "level") return false;
  return regeneratePreviewParams(fields.cmd, fields.enemy, activeGlbUrl) != null;
}

export function buildAssetRunOptions(
  fields: AssetRunFieldState,
  activeGlbUrl: string | null,
  animatedBuildControls: Record<string, AnimatedBuildControlDef[]>,
  animatedBuildOptionValues: Record<string, Record<string, unknown>>,
  regenerate: boolean,
): AssetRunOptions {
  const cfg = CMD_CONFIG[fields.cmd];
  const showEnemy = cfg.showEnemy;
  const singleOutputCmd = fields.cmd === "animated" || fields.cmd === "player" || fields.cmd === "level";

  let buildOptionsJson: string | undefined;
  if (fields.cmd === "animated" && fields.enemy && fields.enemy !== "all") {
    const slug = normalizeAnimatedSlug(fields.enemy);
    const opts = animatedBuildOptionValues[slug];
    if (opts && Object.keys(opts).length > 0) {
      const defs = animatedBuildControls[slug] ?? [];
      const top = partitionAnimatedBuildOptionsForJson(opts, defs);
      const pruned = prunePartitionedBuildOptionsForRun(top, defs);
      buildOptionsJson =
        Object.keys(pruned).length > 0 ? JSON.stringify({ [slug]: pruned }) : undefined;
    }
  }
  if (fields.cmd === "player" && fields.enemy && PLAYER_COLORS.includes(fields.enemy.trim().toLowerCase())) {
    const opts = animatedBuildOptionValues[PLAYER_PROCEDURAL_BUILD_SLUG];
    if (opts && Object.keys(opts).length > 0) {
      const defs = animatedBuildControls[PLAYER_PROCEDURAL_BUILD_SLUG] ?? [];
      const top = partitionAnimatedBuildOptionsForJson(opts, defs);
      const pruned = prunePartitionedBuildOptionsForRun(top, defs);
      buildOptionsJson =
        Object.keys(pruned).length > 0
          ? JSON.stringify({ [PLAYER_PROCEDURAL_BUILD_SLUG]: pruned })
          : undefined;
    }
  }

  const regen = regenerate
    ? regeneratePreviewParams(fields.cmd, showEnemy ? fields.enemy : "", activeGlbUrl)
    : null;
  const previewRel = previewPathFromAssetsUrl(activeGlbUrl);
  const outputDraft =
    regen != null
      ? regen.outputDraft
      : (fields.cmd === "animated" || fields.cmd === "player" || fields.cmd === "level") &&
        previewRel != null &&
        previewRel.includes("/draft/");

  return {
    cmd: fields.cmd,
    enemy: showEnemy ? fields.enemy : undefined,
    count: singleOutputCmd ? 1 : undefined,
    description: cfg.showDescription ? fields.description : undefined,
    difficulty: cfg.showDifficulty ? fields.difficulty : undefined,
    finish: fields.cmd === "player" || fields.cmd === "animated" ? fields.finish : undefined,
    hexColor:
      (fields.cmd === "player" || fields.cmd === "animated") && fields.hexColor
        ? fields.hexColor
        : undefined,
    buildOptionsJson,
    outputDraft,
    replaceVariantIndex: regen?.replaceVariantIndex,
  };
}
