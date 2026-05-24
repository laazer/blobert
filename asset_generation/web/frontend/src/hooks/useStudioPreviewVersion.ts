import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchModelRegistry } from "../api/client";
import { PLAYER_COLORS } from "../components/CommandPanel/commandLogic";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../types";
import { useAppStore } from "../store/useAppStore";
import { normalizeAnimatedSlug } from "../utils/enemyDisplay";
import {
  playerSlimeVersionId,
  playerVariantIndexFromPreviewGlb,
  preferredAnimatedVersionIdFromPreview,
} from "../utils/glbVariants";
import { displayVersionTags } from "../utils/registryTags";

export type StudioPreviewVersionContext = {
  family: string;
  versionId: string;
  version: RegistryEnemyVersion | null;
};

export function useStudioPreviewVersion() {
  const registryReloadSeq = useAppStore((s) => s.registryReloadSeq);
  const commandContext = useAppStore((s) => s.commandContext);
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);

  const [data, setData] = useState<ModelRegistryPayload | null>(null);

  const reload = useCallback(() => {
    fetchModelRegistry()
      .then(setData)
      .catch(() => setData(null));
  }, []);

  useEffect(() => {
    reload();
  }, [reload, registryReloadSeq]);

  const previewContext = useMemo((): StudioPreviewVersionContext | null => {
    if (!data) return null;
    const { cmd, enemy } = commandContext;
    if (cmd === "animated") {
      const family = normalizeAnimatedSlug(enemy);
      if (!family || family === "all") return null;
      const versionId = preferredAnimatedVersionIdFromPreview(family, activeGlbUrl);
      if (!versionId) return null;
      const version = data.enemies[family]?.versions.find((v) => v.id === versionId) ?? null;
      return { family, versionId, version };
    }
    if (cmd === "player") {
      const color = (enemy || "").trim().toLowerCase();
      if (!PLAYER_COLORS.includes(color)) return null;
      const idx = playerVariantIndexFromPreviewGlb(color, activeGlbUrl);
      const versionId = playerSlimeVersionId(color, idx);
      const version = data.player?.versions.find((v) => v.id === versionId) ?? null;
      return { family: "player", versionId, version };
    }
    return null;
  }, [data, commandContext, activeGlbUrl]);

  const versionLabel = useMemo(() => {
    const named = previewContext?.version?.name?.trim();
    if (named) return named;
    if (previewContext?.versionId) return previewContext.versionId;
    return null;
  }, [previewContext]);

  const breadcrumbTags = useMemo(() => {
    if (!previewContext?.version) return [];
    return displayVersionTags(previewContext.version, previewContext.family, new Set([previewContext.family]));
  }, [previewContext]);

  return { previewContext, versionLabel, breadcrumbTags };
}
