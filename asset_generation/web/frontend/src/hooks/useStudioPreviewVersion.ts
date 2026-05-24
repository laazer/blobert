import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchModelRegistry, patchRegistryEnemyVersion } from "../api/client";
import { PLAYER_COLORS } from "../components/CommandPanel/commandLogic";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../types";
import { useAppStore } from "../store/useAppStore";
import { normalizeAnimatedSlug } from "../utils/enemyDisplay";
import {
  playerSlimeVersionId,
  playerVariantIndexFromPreviewGlb,
  preferredAnimatedVersionIdFromPreview,
} from "../utils/glbVariants";
import { collectRegistryTagCatalog, displayVersionTags } from "../utils/registryTags";
import { versionGlbLabel } from "../utils/studioVersionUi";

export type StudioPreviewVersionContext = {
  family: string;
  versionId: string;
  version: RegistryEnemyVersion | null;
};

export function useStudioPreviewVersion() {
  const registryReloadSeq = useAppStore((s) => s.registryReloadSeq);
  const bumpRegistryReload = useAppStore((s) => s.bumpRegistryReload);
  const commandContext = useAppStore((s) => s.commandContext);
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);

  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [saving, setSaving] = useState(false);

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

  const glbLabel = useMemo(() => {
    if (!previewContext?.versionId) return null;
    return versionGlbLabel(previewContext.versionId);
  }, [previewContext?.versionId]);

  const tagCatalog = useMemo(() => (data ? collectRegistryTagCatalog(data) : []), [data]);

  const hideDisplayTags = useMemo(() => {
    if (!previewContext) return new Set<string>();
    return new Set([previewContext.family]);
  }, [previewContext]);

  const patchName = useCallback(
    async (trimmed: string) => {
      if (!previewContext?.version) return;
      const prev = (previewContext.version.name ?? "").trim();
      if (trimmed === prev) return;
      setSaving(true);
      try {
        await patchRegistryEnemyVersion(previewContext.family, previewContext.versionId, {
          name: trimmed === "" ? null : trimmed,
        });
        bumpRegistryReload();
      } finally {
        setSaving(false);
      }
    },
    [previewContext, bumpRegistryReload],
  );

  const patchTags = useCallback(
    async (tags: string[]) => {
      if (!previewContext?.version) return;
      setSaving(true);
      try {
        await patchRegistryEnemyVersion(previewContext.family, previewContext.versionId, { tags });
        bumpRegistryReload();
      } finally {
        setSaving(false);
      }
    },
    [previewContext, bumpRegistryReload],
  );

  return {
    previewContext,
    versionLabel,
    breadcrumbTags,
    glbLabel,
    tagCatalog,
    hideDisplayTags,
    patchName,
    patchTags,
    saving,
  };
}
