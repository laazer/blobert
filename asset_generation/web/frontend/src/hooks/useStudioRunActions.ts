import { useCallback, useMemo } from "react";
import { useAppStore } from "../store/useAppStore";
import { useStreamingOutput } from "../components/Terminal/useStreamingOutput";
import { CMD_CONFIG } from "../components/CommandPanel/commandLogic";
import {
  buildAssetRunOptions,
  canRegenerateAsset,
  validateAssetRun,
  type AssetRunFieldState,
} from "../utils/assetRunOptions";

export function useStudioRunActions(fields: AssetRunFieldState) {
  const isRunning = useAppStore((s) => s.isRunning);
  const isDirty = useAppStore((s) => s.isDirty);
  const saveFile = useAppStore((s) => s.saveFile);
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const animatedBuildControls = useAppStore((s) => s.animatedBuildControls);
  const animatedBuildOptionValues = useAppStore((s) => s.animatedBuildOptionValues);
  const { start } = useStreamingOutput();

  const runValidationError = useMemo(
    () => validateAssetRun(fields, activeGlbUrl),
    [fields, activeGlbUrl],
  );

  const canRegenerate = useMemo(
    () => canRegenerateAsset(fields, activeGlbUrl, runValidationError),
    [fields, activeGlbUrl, runValidationError],
  );

  const canRun = runValidationError == null && !isRunning;

  const regenerateTitle = canRegenerate
    ? "Re-export into the GLB currently shown in the 3D preview (same path and variant index)."
    : "Select cmd/enemy to match the preview export path (animated_exports / player_exports / level_exports GLB).";

  const handleRun = useCallback(
    async (regenerate: boolean) => {
      if (isDirty) await saveFile();
      if (runValidationError) return;
      if (regenerate && !canRegenerate) return;
      start(
        buildAssetRunOptions(
          fields,
          activeGlbUrl,
          animatedBuildControls,
          animatedBuildOptionValues,
          regenerate,
        ),
      );
    },
    [
      isDirty,
      saveFile,
      runValidationError,
      canRegenerate,
      start,
      fields,
      activeGlbUrl,
      animatedBuildControls,
      animatedBuildOptionValues,
    ],
  );

  const handleSave = useCallback(async () => {
    if (isDirty) await saveFile();
  }, [isDirty, saveFile]);

  return {
    isRunning,
    isDirty,
    runValidationError,
    canRegenerate,
    canRun,
    regenerateTitle,
    handleRun,
    handleSave,
    showEnemy: CMD_CONFIG[fields.cmd].showEnemy,
  };
}
