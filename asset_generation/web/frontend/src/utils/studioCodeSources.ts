import type { AnimatedEnemyMeta, RunCmd } from "../types";
import {
  getAnimationCodeExtras,
  getAnimationCodeTarget,
  getModelCodeTarget,
} from "../components/Preview/quickSourceNav";

export type StudioCodeSourceId = "cli" | "model" | "animation" | "keyframes" | "motion";

export const STUDIO_CODE_SOURCE_TABS: readonly { id: StudioCodeSourceId; label: string }[] = [
  { id: "cli", label: "CLI" },
  { id: "model", label: "Model code" },
  { id: "animation", label: "Animation code" },
  { id: "keyframes", label: "Keyframes" },
  { id: "motion", label: "Motion base" },
] as const;

export function resolveStudioCodeSourcePath(
  sourceId: StudioCodeSourceId,
  cmd: RunCmd,
  enemy: string,
  animatedEnemyMeta: readonly AnimatedEnemyMeta[],
): string | null {
  if (sourceId === "cli") return null;
  if (sourceId === "model") return getModelCodeTarget(cmd, enemy, animatedEnemyMeta)?.path ?? null;
  if (sourceId === "animation") return getAnimationCodeTarget(cmd, enemy)?.path ?? null;
  const extras = getAnimationCodeExtras(cmd);
  if (sourceId === "keyframes") {
    return extras.find((t) => t.path.includes("keyframe_system"))?.path ?? null;
  }
  if (sourceId === "motion") {
    return extras.find((t) => t.path.includes("motion_base"))?.path ?? null;
  }
  return null;
}
