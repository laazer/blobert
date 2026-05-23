import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchModelRegistry } from "../api/client";
import type { ModelRegistryPayload } from "../types";
import { useAppStore } from "../store/useAppStore";
import { inferFamilyElementId } from "../utils/inferFamilyElement";
import {
  pickRegistryEnemyFamily,
  REGISTRY_ENEMY_FAMILY_LS,
  registryFamilyTabLabel,
} from "../utils/registryFamilyNav";

export type StudioLibrarySegment = "enemies" | "player" | "level";

export type StudioFamilyRow = {
  id: string;
  label: string;
  versionCount: number;
  elementId: ReturnType<typeof inferFamilyElementId>;
};

export function useStudioEnemyLibrary() {
  const registryReloadSeq = useAppStore((s) => s.registryReloadSeq);
  const commandContext = useAppStore((s) => s.commandContext);
  const setCommandContext = useAppStore((s) => s.setCommandContext);

  const [segment, setSegment] = useState<StudioLibrarySegment>("enemies");
  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);

  const reload = useCallback(() => {
    setError(null);
    fetchModelRegistry()
      .then((registry) => {
        setData(registry);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
      });
  }, []);

  useEffect(() => {
    reload();
  }, [reload, registryReloadSeq]);

  const families = useMemo(
    () => (data ? Object.keys(data.enemies).sort() : []),
    [data],
  );

  const familyRows: StudioFamilyRow[] = useMemo(() => {
    if (!data) return [];
    return families.map((id) => {
      const versions = data.enemies[id]?.versions ?? [];
      return {
        id,
        label: registryFamilyTabLabel(id),
        versionCount: versions.length,
        elementId: inferFamilyElementId(id, versions),
      };
    });
  }, [data, families]);

  const totalVariants = useMemo(
    () => familyRows.reduce((sum, row) => sum + row.versionCount, 0),
    [familyRows],
  );

  const selectFamily = useCallback(
    (familyId: string) => {
      setSelectedFamily(familyId);
      setCommandContext({ cmd: "animated", enemy: familyId });
      try {
        localStorage.setItem(REGISTRY_ENEMY_FAMILY_LS, familyId);
      } catch {
        /* ignore quota / private mode */
      }
    },
    [setCommandContext],
  );

  useEffect(() => {
    if (segment !== "enemies" || families.length === 0) return;
    const commandEnemy = commandContext.cmd === "animated" ? commandContext.enemy : undefined;
    setSelectedFamily((prev) => pickRegistryEnemyFamily(families, prev, commandEnemy));
  }, [data, families, segment, commandContext.cmd, commandContext.enemy]);

  return {
    segment,
    setSegment,
    data,
    error,
    reload,
    families,
    familyRows,
    selectedFamily,
    selectFamily,
    totalVariants,
  };
}
