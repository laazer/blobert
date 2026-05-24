import { useCallback, useEffect, useMemo, useState } from "react";
import { PLAYER_COLORS } from "../components/CommandPanel/commandLogic";
import { fetchModelRegistry } from "../api/client";
import type { ModelRegistryPayload } from "../types";
import { useAppStore } from "../store/useAppStore";
import { inferFamilyElementId } from "../utils/inferFamilyElement";
import {
  pickRegistryEnemyFamily,
  REGISTRY_ENEMY_FAMILY_LS,
  registryFamilyTabLabel,
} from "../utils/registryFamilyNav";
import {
  countPlayerVersionsByColor,
  pickRegistryPlayerColor,
  playerColorElementId,
  playerColorLabel,
  REGISTRY_PLAYER_COLOR_LS,
} from "../utils/studioPlayerLibrary";

export type StudioLibrarySegment = "enemies" | "player" | "level";

export type StudioFamilyRow = {
  id: string;
  label: string;
  versionCount: number;
  elementId: ReturnType<typeof inferFamilyElementId>;
};

export type StudioPlayerColorRow = {
  id: string;
  label: string;
  versionCount: number;
  elementId: ReturnType<typeof playerColorElementId>;
};

export function useStudioEnemyLibrary() {
  const registryReloadSeq = useAppStore((s) => s.registryReloadSeq);
  const commandContext = useAppStore((s) => s.commandContext);
  const setCommandContext = useAppStore((s) => s.setCommandContext);

  const [segment, setSegmentState] = useState<StudioLibrarySegment>("enemies");
  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);
  const [selectedPlayerColor, setSelectedPlayerColor] = useState<string | null>(null);

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

  const playerVersions = data?.player?.versions ?? [];

  const playerColorRows: StudioPlayerColorRow[] = useMemo(() => {
    const counts = countPlayerVersionsByColor(playerVersions);
    return PLAYER_COLORS.map((id) => ({
      id,
      label: playerColorLabel(id),
      versionCount: counts[id] ?? 0,
      elementId: playerColorElementId(id),
    }));
  }, [playerVersions]);

  const totalVariants = useMemo(
    () => familyRows.reduce((sum, row) => sum + row.versionCount, 0),
    [familyRows],
  );

  const totalPlayerVariants = useMemo(
    () => playerVersions.length,
    [playerVersions],
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

  const selectPlayerColor = useCallback(
    (colorId: string) => {
      const color = colorId.trim().toLowerCase();
      setSelectedPlayerColor(color);
      setCommandContext({ cmd: "player", enemy: color });
      try {
        localStorage.setItem(REGISTRY_PLAYER_COLOR_LS, color);
      } catch {
        /* ignore */
      }
    },
    [setCommandContext],
  );

  const setSegment = useCallback(
    (next: StudioLibrarySegment) => {
      setSegmentState(next);
      if (next === "player") {
        const color = pickRegistryPlayerColor(
          PLAYER_COLORS,
          selectedPlayerColor,
          commandContext.cmd === "player" ? commandContext.enemy : undefined,
        );
        if (color) selectPlayerColor(color);
        else setCommandContext({ cmd: "player", enemy: PLAYER_COLORS[0] });
      } else if (next === "enemies" && families.length > 0) {
        const family = pickRegistryEnemyFamily(
          families,
          selectedFamily,
          commandContext.cmd === "animated" ? commandContext.enemy : undefined,
        );
        if (family) selectFamily(family);
      }
    },
    [
      selectPlayerColor,
      selectFamily,
      selectedPlayerColor,
      selectedFamily,
      commandContext.cmd,
      commandContext.enemy,
      families,
      setCommandContext,
    ],
  );

  useEffect(() => {
    if (segment !== "enemies" || families.length === 0) return;
    const commandEnemy = commandContext.cmd === "animated" ? commandContext.enemy : undefined;
    setSelectedFamily((prev) => pickRegistryEnemyFamily(families, prev, commandEnemy));
  }, [data, families, segment, commandContext.cmd, commandContext.enemy]);

  useEffect(() => {
    if (segment !== "player") return;
    const commandColor = commandContext.cmd === "player" ? commandContext.enemy : undefined;
    setSelectedPlayerColor((prev) =>
      pickRegistryPlayerColor(PLAYER_COLORS, prev, commandColor),
    );
  }, [segment, commandContext.cmd, commandContext.enemy]);

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
    playerColorRows,
    selectedPlayerColor,
    selectPlayerColor,
    totalPlayerVariants,
    playerVersions,
  };
}
