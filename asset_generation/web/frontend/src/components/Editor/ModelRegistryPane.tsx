import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  deleteRegistryEnemyVersion,
  fetchLoadExistingCandidates,
  fetchEnemyFamilySlots,
  fetchModelRegistry,
  openExistingRegistryModel,
  patchRegistryEnemyVersion,
  patchRegistryPlayerActiveVisual,
  postSyncDiscoveredAnimatedGlbVersions,
  putEnemyFamilySlots,
  type LoadExistingCandidate,
  type DeleteEnemyVersionRequest,
} from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import { preferredAnimatedVersionIdFromPreview } from "../../utils/glbVariants";
import { buildPlayerModelSelectOptions, playerExportGlbPathsFromAssets } from "../../utils/registryPlayerModelOptions";
import { canAddEnemySlot, nextEnemySlotsAfterAdd, nextEnemySlotsAfterRemove } from "../../utils/registrySlotOps";
import { AddEnemySlotModal } from "./AddEnemySlotModal";
import { PlayerActiveModelModal } from "./PlayerActiveModelModal";
import { RegistryEnemyFamiliesSection } from "./RegistryEnemyFamiliesSection";
import { RegistryPlayerSection } from "./RegistryPlayerSection";
import type { EnemyDeletePlan } from "./registryEnemyTypes";
import { loadExistingCandidateKey, toOpenExistingRequest } from "./registryLoadExisting";
import {
  DRAFT_DELETE_CONFIRM_COPY,
  IN_USE_DELETE_CONFIRM_COPY,
} from "./registryPaneStrings";

export { loadExistingCandidateKey, loadExistingCandidateLabel, toOpenExistingRequest } from "./registryLoadExisting";
export {
  DRAFT_DELETE_CONFIRM_COPY,
  ENEMY_EMPTY_SLOTS_COPY,
  IN_USE_DELETE_CONFIRM_COPY,
  LOAD_EXISTING_EMPTY_COPY,
  PLAYER_RESTART_REQUIREMENT_COPY,
} from "./registryPaneStrings";
export type { EnemyDeletePlan } from "./registryEnemyTypes";
export { nextEnemySlotsAfterAdd, nextEnemySlotsAfterRemove, canAddEnemySlot } from "../../utils/registrySlotOps";

const noteStyle = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };

export function buildEnemyDeletePlan(family: string, version: Pick<RegistryEnemyVersion, "id" | "draft" | "in_use">): EnemyDeletePlan | null {
  const isDraft = version.draft;
  const isInUse = version.in_use && !version.draft;
  if (!isDraft && !isInUse) return null;
  const confirmTextPrefix = isDraft ? "delete draft" : "delete in-use";
  return {
    confirmMessage: isDraft ? DRAFT_DELETE_CONFIRM_COPY : IN_USE_DELETE_CONFIRM_COPY,
    request: {
      confirm: true,
      delete_files: isDraft,
      confirm_text: `${confirmTextPrefix} ${family} ${version.id}`,
    },
  };
}

export async function executeEnemyDeleteFlow(args: {
  family: string;
  version: Pick<RegistryEnemyVersion, "id" | "draft" | "in_use">;
  confirmDelete: (message: string) => boolean;
  onDelete: (family: string, versionId: string, body: DeleteEnemyVersionRequest) => Promise<ModelRegistryPayload>;
  onSuccess: (nextRegistry: ModelRegistryPayload) => Promise<void> | void;
  onError: (message: string) => void;
}): Promise<"cancelled" | "deleted" | "failed"> {
  const plan = buildEnemyDeletePlan(args.family, args.version);
  if (!plan) return "failed";
  if (!args.confirmDelete(plan.confirmMessage)) {
    return "cancelled";
  }
  try {
    const nextRegistry = await args.onDelete(args.family, args.version.id, plan.request);
    await args.onSuccess(nextRegistry);
    return "deleted";
  } catch (e: unknown) {
    args.onError(e instanceof Error ? e.message : String(e));
    return "failed";
  }
}

export function ModelRegistryPane() {
  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [deleteBusyKey, setDeleteBusyKey] = useState<string | null>(null);
  const [slotVersionIdsByFamily, setSlotVersionIdsByFamily] = useState<Record<string, string[]>>({});
  const [slotSaveBusyFamily, setSlotSaveBusyFamily] = useState<string | null>(null);
  const [loadExistingCandidates, setLoadExistingCandidates] = useState<LoadExistingCandidate[]>([]);
  const [loadExistingSelection, setLoadExistingSelection] = useState<string>("");
  const [loadExistingBusy, setLoadExistingBusy] = useState<boolean>(false);
  const [playerPickOpen, setPlayerPickOpen] = useState(false);
  const [addSlotFamily, setAddSlotFamily] = useState<string | null>(null);
  const [addSlotBusyFamily, setAddSlotBusyFamily] = useState<string | null>(null);
  const [addSlotPreparingFamily, setAddSlotPreparingFamily] = useState<string | null>(null);

  const selectAssetByPath = useAppStore((s) => s.selectAssetByPath);
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const assets = useAppStore((s) => s.assets);
  const loadAssets = useAppStore((s) => s.loadAssets);

  const loadEnemySlots = useCallback(async (registry: ModelRegistryPayload) => {
    const families = Object.keys(registry.enemies);
    if (families.length === 0) {
      setSlotVersionIdsByFamily({});
      return;
    }
    const entries = await Promise.all(
      families.map(async (family) => {
        const slotPayload = await fetchEnemyFamilySlots(family);
        return [family, slotPayload.version_ids] as const;
      }),
    );
    setSlotVersionIdsByFamily(Object.fromEntries(entries));
  }, []);

  const syncFromRegistry = useCallback(
    async (registry: ModelRegistryPayload) => {
      setData(registry);
      await loadEnemySlots(registry);
      const candidatePayload = await fetchLoadExistingCandidates();
      const candidates = candidatePayload.candidates;
      setLoadExistingCandidates(candidates);
      setLoadExistingSelection((prev) => {
        if (!candidates.some((row) => loadExistingCandidateKey(row) === prev)) {
          return candidates.length > 0 ? loadExistingCandidateKey(candidates[0]) : "";
        }
        return prev;
      });
    },
    [loadEnemySlots],
  );

  const reload = useCallback(() => {
    setError(null);
    fetchModelRegistry()
      .then((registry) => syncFromRegistry(registry))
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
      });
  }, [syncFromRegistry]);

  useEffect(() => {
    reload();
  }, [reload]);

  const families = useMemo(
    () => (data ? Object.keys(data.enemies).sort() : []),
    [data],
  );
  const playerCandidates = useMemo(() => {
    if (!data) return [] as { family: string; id: string; path: string }[];
    const rows: { family: string; id: string; path: string }[] = [];
    for (const family of families) {
      for (const version of data.enemies[family].versions) {
        if (!version.draft && version.path.endsWith(".glb")) {
          rows.push({ family, id: version.id, path: version.path });
        }
      }
    }
    return rows;
  }, [data, families]);

  const playerModelOptions = useMemo(
    () =>
      buildPlayerModelSelectOptions(
        data,
        playerCandidates,
        playerExportGlbPathsFromAssets(assets),
      ),
    [data, playerCandidates, assets],
  );

  const familyAddSlotDisabled = useMemo(() => {
    if (!data) return {} as Record<string, boolean>;
    const out: Record<string, boolean> = {};
    for (const family of families) {
      const versions = data.enemies[family].versions;
      const cur = slotVersionIdsByFamily[family] ?? [];
      out[family] = !canAddEnemySlot(cur, versions);
    }
    return out;
  }, [data, families, slotVersionIdsByFamily]);

  useEffect(() => {
    if (playerPickOpen) void loadAssets();
  }, [playerPickOpen, loadAssets]);

  async function applyFlags(family: string, v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) {
    const key = `${family}:${v.id}`;
    setBusyKey(key);
    setError(null);
    try {
      const use = nextDraft ? false : nextInUse;
      const updated = await patchRegistryEnemyVersion(family, v.id, {
        draft: nextDraft,
        in_use: use,
      });
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  async function applyPlayerSelection(path: string) {
    setBusyKey("player_active_visual");
    setError(null);
    try {
      const updated = await patchRegistryPlayerActiveVisual({ path });
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  async function requestAddSlotModal(family: string) {
    if (addSlotPreparingFamily) return;
    setAddSlotPreparingFamily(family);
    setError(null);
    try {
      const updated = await postSyncDiscoveredAnimatedGlbVersions(family);
      await syncFromRegistry(updated);
      setAddSlotFamily(family);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAddSlotPreparingFamily(null);
    }
  }

  async function confirmAddEnemySlot(family: string, versionId: string) {
    if (!data) return;
    const row = data.enemies[family]?.versions.find((v) => v.id === versionId);
    if (!row || row.draft) return;
    setAddSlotBusyFamily(family);
    setError(null);
    try {
      if (!row.in_use) {
        const updated = await patchRegistryEnemyVersion(family, versionId, { in_use: true });
        await syncFromRegistry(updated);
      }
      setSlotVersionIdsByFamily((prev) => {
        const cur = [...(prev[family] ?? [])];
        if (cur.includes(versionId)) return prev;
        return { ...prev, [family]: [...cur, versionId] };
      });
      setAddSlotFamily(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAddSlotBusyFamily(null);
    }
  }

  function removeEnemySlot(family: string, index: number) {
    setSlotVersionIdsByFamily((prev) => {
      const current = prev[family] ?? [];
      return { ...prev, [family]: nextEnemySlotsAfterRemove(current, index) };
    });
  }

  function updateEnemySlotVersion(family: string, index: number, versionId: string) {
    setSlotVersionIdsByFamily((prev) => {
      const current = [...(prev[family] ?? [])];
      current[index] = versionId;
      return { ...prev, [family]: current };
    });
  }

  async function saveEnemySlots(family: string) {
    setSlotSaveBusyFamily(family);
    setError(null);
    try {
      const ids = slotVersionIdsByFamily[family] ?? [];
      const payload = await putEnemyFamilySlots(family, ids);
      setSlotVersionIdsByFamily((prev) => ({ ...prev, [family]: payload.version_ids }));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      await reload();
    } finally {
      setSlotSaveBusyFamily(null);
    }
  }

  async function openExistingSelection() {
    if (loadExistingBusy) return;
    const row = loadExistingCandidates.find((candidate) => loadExistingCandidateKey(candidate) === loadExistingSelection);
    if (!row) return;
    setLoadExistingBusy(true);
    setError(null);
    try {
      const payload = await openExistingRegistryModel(toOpenExistingRequest(row));
      selectAssetByPath(payload.path);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadExistingBusy(false);
    }
  }

  async function deleteEnemyVersion(family: string, version: RegistryEnemyVersion) {
    const key = `${family}:${version.id}`;
    setDeleteBusyKey(key);
    setError(null);
    try {
      await executeEnemyDeleteFlow({
        family,
        version,
        confirmDelete: (message) => window.confirm(message),
        onDelete: deleteRegistryEnemyVersion,
        onSuccess: syncFromRegistry,
        onError: (message) => setError(message),
      });
    } finally {
      setDeleteBusyKey(null);
    }
  }

  if (!data && !error) {
    return (
      <div style={{ padding: 16, color: "#9d9d9d", fontSize: 12 }}>
        Loading model registry…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ color: "#f14c4c", fontSize: 12, marginBottom: 8 }}>{error}</div>
        <button type="button" onClick={reload} style={btnSecondary}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const playerBusy = busyKey === "player_active_visual";

  return (
    <div style={{ padding: 12, color: "#d4d4d4", fontSize: 12, overflow: "auto", flex: 1 }}>
      <RegistryPlayerSection
        activeGamePath={data.player_active_visual?.path ?? null}
        playerBusy={playerBusy}
        onOpenPickGameActive={() => setPlayerPickOpen(true)}
        loadExistingCandidates={loadExistingCandidates}
        loadExistingSelection={loadExistingSelection}
        onLoadExistingSelectionChange={setLoadExistingSelection}
        loadExistingBusy={loadExistingBusy}
        onLoadExistingInPreview={openExistingSelection}
        onPreviewGameActive={() => {
          const p = data.player_active_visual?.path;
          if (p) selectAssetByPath(p);
        }}
      />

      <RegistryEnemyFamiliesSection
        families={families}
        enemies={data.enemies}
        slotVersionIdsByFamily={slotVersionIdsByFamily}
        familyAddSlotDisabled={familyAddSlotDisabled}
        addSlotPreparingFamily={addSlotPreparingFamily}
        slotSaveBusyFamily={slotSaveBusyFamily}
        busyKey={busyKey}
        deleteBusyKey={deleteBusyKey}
        onAddSlot={requestAddSlotModal}
        onRemoveSlot={removeEnemySlot}
        onUpdateSlotVersion={updateEnemySlotVersion}
        onSaveSlots={saveEnemySlots}
        onApplyFlags={applyFlags}
        onDeleteVersion={deleteEnemyVersion}
        getEnemyDeletePlan={buildEnemyDeletePlan}
      />

      <PlayerActiveModelModal
        open={playerPickOpen}
        options={playerModelOptions}
        currentPath={data.player_active_visual?.path ?? null}
        busy={playerBusy}
        onClose={() => setPlayerPickOpen(false)}
        onPick={async (path) => {
          await applyPlayerSelection(path);
          setPlayerPickOpen(false);
        }}
      />

      {addSlotFamily && (
        <AddEnemySlotModal
          open
          family={addSlotFamily}
          versions={data.enemies[addSlotFamily]?.versions ?? []}
          slotVersionIds={slotVersionIdsByFamily[addSlotFamily] ?? []}
          preferredVersionId={preferredAnimatedVersionIdFromPreview(addSlotFamily, activeGlbUrl)}
          busy={addSlotBusyFamily === addSlotFamily}
          onClose={() => setAddSlotFamily(null)}
          onPick={(versionId) => confirmAddEnemySlot(addSlotFamily, versionId)}
        />
      )}

      {error && (
        <div style={{ color: "#f14c4c", marginBottom: 8, fontSize: 11 }}>{error}</div>
      )}
      <div style={{ marginTop: 16, ...noteStyle }}>
        Persisted to <code style={{ color: "#ce9178" }}>asset_generation/python/model_registry.json</code> via API
        (atomic write; only this manifest path is modified).
      </div>
    </div>
  );
}

const btnSecondary: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
