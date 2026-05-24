import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import type { RunCmd } from "../../types";
import { ALL_CMDS } from "../CommandPanel/commandLogic";
import { centerPanelTabBtnStyle } from "../layout/centerPanelTabStyles";
import { STUDIO_INK_MUTED, STUDIO_INK_SECONDARY } from "../../styles/studioTokens";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import {
  deleteRegistryEnemyVersion,
  fetchLoadExistingCandidates,
  fetchEnemyFamilySlots,
  fetchModelRegistry,
  openExistingRegistryModel,
  patchRegistryEnemyVersion,
  postSyncDiscoveredAnimatedGlbVersions,
  postSyncDiscoveredPlayerGlbVersions,
  putEnemyFamilySlots,
  type LoadExistingCandidate,
  type DeleteEnemyVersionRequest,
} from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import { preferredAnimatedVersionIdFromPreview, preferredPlayerVersionIdFromPreview } from "../../utils/glbVariants";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { filterVersionsByPlayerColor } from "../../utils/studioPlayerLibrary";
import { StudioPlayerVersionsPanel } from "../studio/StudioPlayerVersionsPanel";
import { canAddEnemySlot, nextEnemySlotsAfterAdd, nextEnemySlotsAfterRemove } from "../../utils/registrySlotOps";
import {
  REGISTRY_ENEMY_FAMILY_LS,
  pickRegistryEnemyFamily,
  registryFamilyTabLabel,
} from "../../utils/registryFamilyNav";
import {
  enemyRegistryRowKey,
  parseEnemyRegistryRowKey,
  pruneEnemyVersionSelectionKeys,
} from "../../utils/registryVersionSelection";
import {
  REGISTRY_TAG_FILTER_LS,
  REGISTRY_TAG_GROUP_LS,
  collectRegistryTagCatalog,
  filterFamiliesByTags,
  groupFamiliesByTag,
  parseSavedTagFilter,
  parseSavedTagGroup,
} from "../../utils/registryTags";
import { AddEnemySlotModal } from "./AddEnemySlotModal";
import { RegistryEnemyFamilyPanel } from "./RegistryEnemyFamilyPanel";
import { StudioEnemyVersionsPanel } from "../studio/StudioEnemyVersionsPanel";
import { RegistryEnemyLoadExistingSection } from "./RegistryEnemyLoadExistingSection";
import { RegistryPlayerPowerTypesSection } from "./RegistryPlayerPowerTypesSection";
import { RegistryTagOrganizerBar } from "./RegistryTagOrganizerBar";
import type { EnemyDeletePlan } from "./registryEnemyTypes";
import { loadExistingCandidateKey, toOpenExistingRequest } from "./registryLoadExisting";
import {
  DRAFT_DELETE_CONFIRM_COPY,
  IN_USE_DELETE_CONFIRM_COPY,
} from "./registryPaneStrings";

export {
  filterLoadExistingCandidates,
  loadExistingCandidateKey,
  loadExistingCandidateLabel,
  toOpenExistingRequest,
} from "./registryLoadExisting";
export {
  DRAFT_DELETE_CONFIRM_COPY,
  ENEMY_EMPTY_SLOTS_COPY,
  IN_USE_DELETE_CONFIRM_COPY,
  LOAD_EXISTING_EMPTY_COPY,
} from "./registryPaneStrings";
export type { EnemyDeletePlan } from "./registryEnemyTypes";
export { nextEnemySlotsAfterAdd, nextEnemySlotsAfterRemove, canAddEnemySlot } from "../../utils/registrySlotOps";
export { PLAYER_POWER_TYPES_HEADING } from "./RegistryPlayerPowerTypesSection";

const REGISTRY_SUBTAB_LS = "blobert.registry.subtab";

function parseSavedRegistrySubtab(): RunCmd | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(REGISTRY_SUBTAB_LS);
    if (!raw) return null;
    if (!ALL_CMDS.includes(raw as RunCmd)) return null;
    return raw as RunCmd;
  } catch {
    return null;
  }
}

function registrySubtabLabel(cmd: RunCmd): string {
  if (cmd === "animated") return "Enemies";
  return cmd.slice(0, 1).toUpperCase() + cmd.slice(1);
}

const noteStyle = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };

export type ModelRegistryPaneProps = {
  /** Studio Versions inspector: scoped to command bar context, no legacy subtab chrome. */
  studioSurface?: boolean;
};

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

export function ModelRegistryPane({ studioSurface = false }: ModelRegistryPaneProps) {
  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [deleteBusyKey, setDeleteBusyKey] = useState<string | null>(null);
  const [slotVersionIdsByFamily, setSlotVersionIdsByFamily] = useState<Record<string, string[]>>({});
  const [slotSaveBusyFamily, setSlotSaveBusyFamily] = useState<string | null>(null);
  const [loadExistingCandidates, setLoadExistingCandidates] = useState<LoadExistingCandidate[]>([]);
  const [loadExistingSelection, setLoadExistingSelection] = useState<string>("");
  const [loadExistingBusy, setLoadExistingBusy] = useState<boolean>(false);
  const [playerScanBusy, setPlayerScanBusy] = useState(false);
  const [addSlotFamily, setAddSlotFamily] = useState<string | null>(null);
  const [addSlotBusyFamily, setAddSlotBusyFamily] = useState<string | null>(null);
  const [addSlotPreparingFamily, setAddSlotPreparingFamily] = useState<string | null>(null);
  const [registrySubtab, setRegistrySubtab] = useState<RunCmd>(() => parseSavedRegistrySubtab() ?? "animated");
  const [selectedEnemyFamily, setSelectedEnemyFamily] = useState<string | null>(null);
  const [selectedEnemyVersionKeys, setSelectedEnemyVersionKeys] = useState<Set<string>>(() => new Set());
  const [bulkEnemyBusyFamily, setBulkEnemyBusyFamily] = useState<string | null>(null);
  const [tagFilter, setTagFilter] = useState<Set<string>>(() => new Set(parseSavedTagFilter()));
  const [groupByTag, setGroupByTag] = useState<string | null>(() => parseSavedTagGroup());

  const selectAssetByPath = useAppStore((s) => s.selectAssetByPath);
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const registryReloadSeq = useAppStore((s) => s.registryReloadSeq);
  const commandContext = useAppStore((s) => s.commandContext);

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
      setSelectedEnemyVersionKeys((prev) => pruneEnemyVersionSelectionKeys(prev, registry.enemies));
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
  }, [reload, registryReloadSeq]);

  useEffect(() => {
    try {
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(REGISTRY_SUBTAB_LS, registrySubtab);
      }
    } catch {
      /* ignore quota / private mode */
    }
  }, [registrySubtab]);

  const families = useMemo(
    () => (data ? Object.keys(data.enemies).sort() : []),
    [data],
  );

  const commandEnemyForFamily =
    commandContext.cmd === "animated" ? commandContext.enemy : undefined;

  const studioPlayerColor = useMemo(() => {
    if (!studioSurface || commandContext.cmd !== "player") return null;
    const c = commandContext.enemy.trim().toLowerCase();
    return PLAYER_COLORS.includes(c) ? c : null;
  }, [studioSurface, commandContext.cmd, commandContext.enemy]);

  const studioPlayerVersions = useMemo(() => {
    if (!studioPlayerColor || !data?.player?.versions) return [];
    return filterVersionsByPlayerColor(data.player.versions, studioPlayerColor);
  }, [data, studioPlayerColor]);

  useEffect(() => {
    if (!studioSurface) return;
    const { cmd, enemy } = commandContext;
    if (cmd === "animated") {
      setRegistrySubtab("animated");
      const slug = normalizeAnimatedSlug(enemy);
      if (slug && slug !== "all") {
        setSelectedEnemyFamily(slug);
      }
      return;
    }
    if (cmd === "player") {
      setRegistrySubtab("player");
      setSelectedEnemyFamily(null);
    }
  }, [studioSurface, commandContext.cmd, commandContext.enemy]);

  const tagCatalog = useMemo(
    () => (data ? collectRegistryTagCatalog(data) : []),
    [data],
  );

  const visibleFamilies = useMemo(
    () => (data ? filterFamiliesByTags(families, data.enemies, [...tagFilter]) : []),
    [families, data, tagFilter],
  );

  const familyGroups = useMemo(() => {
    if (!groupByTag || !data) return null;
    return groupFamiliesByTag(visibleFamilies, data.enemies, groupByTag);
  }, [groupByTag, visibleFamilies, data]);

  const hideDisplayTags = useMemo(() => {
    const hidden = new Set<string>();
    if (selectedEnemyFamily) hidden.add(selectedEnemyFamily);
    if (groupByTag) hidden.add(groupByTag);
    return hidden;
  }, [selectedEnemyFamily, groupByTag]);

  useEffect(() => {
    if (registrySubtab !== "animated" || visibleFamilies.length === 0) return;
    setSelectedEnemyFamily((prev) =>
      pickRegistryEnemyFamily(visibleFamilies, prev, commandEnemyForFamily),
    );
  }, [visibleFamilies, registrySubtab, commandEnemyForFamily]);

  useEffect(() => {
    if (registrySubtab !== "animated" || !selectedEnemyFamily) return;
    try {
      localStorage.setItem(REGISTRY_ENEMY_FAMILY_LS, selectedEnemyFamily);
    } catch {
      /* ignore quota / private mode */
    }
  }, [registrySubtab, selectedEnemyFamily]);

  useEffect(() => {
    try {
      localStorage.setItem(REGISTRY_TAG_FILTER_LS, JSON.stringify([...tagFilter]));
    } catch {
      /* ignore */
    }
  }, [tagFilter]);

  useEffect(() => {
    try {
      if (groupByTag) localStorage.setItem(REGISTRY_TAG_GROUP_LS, groupByTag);
      else localStorage.removeItem(REGISTRY_TAG_GROUP_LS);
    } catch {
      /* ignore */
    }
  }, [groupByTag]);

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

  function previewVersion(_family: string, v: RegistryEnemyVersion) {
    selectAssetByPath(v.path);
  }

  function toggleEnemyVersionSelect(family: string, versionId: string) {
    const k = enemyRegistryRowKey(family, versionId);
    setSelectedEnemyVersionKeys((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  }

  function setEnemyFamilySelectAllVersions(family: string, nextChecked: boolean) {
    if (!data) return;
    const versions = data.enemies[family]?.versions ?? [];
    setSelectedEnemyVersionKeys((prev) => {
      const next = new Set(prev);
      for (const v of versions) {
        const k = enemyRegistryRowKey(family, v.id);
        if (nextChecked) next.add(k);
        else next.delete(k);
      }
      return next;
    });
  }

  function clearEnemyFamilySelection(family: string) {
    setSelectedEnemyVersionKeys((prev) => {
      const next = new Set(prev);
      for (const k of [...next]) {
        if (k.startsWith(`${family}:`)) next.delete(k);
      }
      return next;
    });
  }

  async function bulkEnemyApplyFlags(family: string, nextDraft: boolean, nextInUse: boolean) {
    if (!data) return;
    const keys = [...selectedEnemyVersionKeys].filter((k) => k.startsWith(`${family}:`));
    const rows: RegistryEnemyVersion[] = [];
    for (const k of keys) {
      const p = parseEnemyRegistryRowKey(k);
      if (!p || p.family !== family) continue;
      const v = data.enemies[family]?.versions.find((x) => x.id === p.versionId);
      if (v) rows.push(v);
    }
    if (rows.length === 0) return;
    setBulkEnemyBusyFamily(family);
    setError(null);
    try {
      let nextRegistry: ModelRegistryPayload = data;
      for (const row of rows) {
        const use = nextDraft ? false : nextInUse;
        nextRegistry = await patchRegistryEnemyVersion(family, row.id, {
          draft: nextDraft,
          in_use: use,
        });
      }
      await syncFromRegistry(nextRegistry);
      clearEnemyFamilySelection(family);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBulkEnemyBusyFamily(null);
    }
  }

  async function bulkDeleteEnemyVersions(family: string) {
    if (!data) return;
    const keys = [...selectedEnemyVersionKeys].filter((k) => k.startsWith(`${family}:`));
    const rows: RegistryEnemyVersion[] = [];
    for (const k of keys) {
      const p = parseEnemyRegistryRowKey(k);
      if (!p || p.family !== family) continue;
      const v = data.enemies[family]?.versions.find((x) => x.id === p.versionId);
      if (v && buildEnemyDeletePlan(family, v)) rows.push(v);
    }
    if (rows.length === 0) {
      window.alert(
        "No deletable versions selected. Only draft or in-pool rows can be deleted from this table.",
      );
      return;
    }
    const drafts = rows.filter((r) => r.draft).length;
    const inPool = rows.filter((r) => r.in_use && !r.draft).length;
    const msg = `Delete ${rows.length} version(s)? ${drafts} draft (files may be removed), ${inPool} in pool (spawn rules apply).`;
    if (!window.confirm(msg)) return;
    setBulkEnemyBusyFamily(family);
    setError(null);
    try {
      let nextRegistry: ModelRegistryPayload = data;
      for (const v of rows) {
        const plan = buildEnemyDeletePlan(family, v);
        if (!plan) continue;
        nextRegistry = await deleteRegistryEnemyVersion(family, v.id, plan.request);
      }
      await syncFromRegistry(nextRegistry);
      clearEnemyFamilySelection(family);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      await reload();
    } finally {
      setBulkEnemyBusyFamily(null);
    }
  }

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

  async function applyPlayerVersionFlags(v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) {
    const key = `player:${v.id}`;
    setBusyKey(key);
    setError(null);
    try {
      const use = nextDraft ? false : nextInUse;
      const updated = await patchRegistryEnemyVersion("player", v.id, { draft: nextDraft, in_use: use });
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  async function patchVersionTags(family: string, v: RegistryEnemyVersion, tags: string[]) {
    const key = `${family}:${v.id}`;
    setBusyKey(key);
    setError(null);
    try {
      const updated = await patchRegistryEnemyVersion(family, v.id, { tags });
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  async function renameRegistryVersion(family: string, v: RegistryEnemyVersion, trimmed: string) {
    const prev = (v.name ?? "").trim();
    if (trimmed === prev) return;
    const key = `${family}:${v.id}`;
    setBusyKey(key);
    setError(null);
    try {
      const updated = await patchRegistryEnemyVersion(family, v.id, {
        name: trimmed === "" ? null : trimmed,
      });
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  async function scanPlayerExports() {
    if (playerScanBusy) return;
    setPlayerScanBusy(true);
    setError(null);
    try {
      const updated = await postSyncDiscoveredPlayerGlbVersions();
      await syncFromRegistry(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPlayerScanBusy(false);
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

  function addEmptyEnemySlot(family: string) {
    setSlotVersionIdsByFamily((prev) => {
      const cur = [...(prev[family] ?? [])];
      return { ...prev, [family]: [...cur, ""] };
    });
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
      selectAssetByPath(payload.path, {
        importBuildOptions: true,
        registryBuildOptions: payload.build_options,
      });
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
      <div
        style={{
          padding: studioSurface ? 0 : 16,
          color: studioSurface ? STUDIO_INK_MUTED : "#9d9d9d",
          fontSize: 12,
        }}
        data-testid={studioSurface ? "studio-versions-loading" : undefined}
      >
        Loading model registry…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ padding: studioSurface ? 0 : 16 }} data-testid={studioSurface ? "studio-versions-error" : undefined}>
        <div style={{ color: "#f14c4c", fontSize: 12, marginBottom: 8 }}>{error}</div>
        <button type="button" onClick={reload} style={btnSecondary}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const playerVersions = data.player?.versions ?? [];

  const familyTabListStyle: CSSProperties = {
    display: "flex",
    gap: 6,
    marginBottom: 10,
    flexWrap: "nowrap",
    overflowX: "auto",
    paddingBottom: 2,
  };

  const renderFamilyTab = (family: string) => (
    <button
      key={family}
      type="button"
      role="tab"
      aria-selected={selectedEnemyFamily === family}
      id={`registry-family-tab-${family}`}
      data-testid={`registry-family-tab-${family}`}
      style={{
        ...centerPanelTabBtnStyle(selectedEnemyFamily === family),
        flexShrink: 0,
      }}
      onClick={() => setSelectedEnemyFamily(family)}
    >
      {registryFamilyTabLabel(family)}
    </button>
  );

  return (
    <div
      style={{
        padding: studioSurface ? 0 : 12,
        color: studioSurface ? STUDIO_INK_SECONDARY : "#d4d4d4",
        fontSize: 12,
        overflow: studioSurface ? "visible" : "auto",
        flex: studioSurface ? undefined : 1,
      }}
      data-testid={studioSurface ? "studio-versions-controls" : undefined}
    >
      {!studioSurface ? (
      <div
        style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}
        role="tablist"
        aria-label="Registry categories"
      >
        {ALL_CMDS.map((cmd) => (
          <button
            key={cmd}
            type="button"
            role="tab"
            aria-selected={registrySubtab === cmd}
            id={`registry-subtab-${cmd}`}
            style={centerPanelTabBtnStyle(registrySubtab === cmd)}
            onClick={() => setRegistrySubtab(cmd)}
          >
            {registrySubtabLabel(cmd)}
          </button>
        ))}
      </div>
      ) : null}

      {registrySubtab === "animated" ? (
        <>
          {!studioSurface && families.length > 0 ? (
            <RegistryTagOrganizerBar
              catalog={tagCatalog}
              filterTags={tagFilter}
              groupByTag={groupByTag}
              onToggleFilter={(tag) => {
                setTagFilter((prev) => {
                  const next = new Set(prev);
                  if (next.has(tag)) next.delete(tag);
                  else next.add(tag);
                  return next;
                });
              }}
              onClearFilters={() => setTagFilter(new Set())}
              onGroupByChange={setGroupByTag}
            />
          ) : null}
          {!studioSurface && visibleFamilies.length > 0 ? (
            familyGroups ? (
              familyGroups.map((group) => (
                <div key={group.tag} style={{ marginBottom: 8 }}>
                  <div
                    style={{
                      fontSize: 10,
                      color: "#888",
                      marginBottom: 4,
                      fontWeight: 600,
                    }}
                  >
                    {group.label}
                  </div>
                  <div style={familyTabListStyle} role="tablist" aria-label={`Families: ${group.label}`}>
                    {group.families.map((family) => renderFamilyTab(family))}
                  </div>
                </div>
              ))
            ) : (
              <div style={familyTabListStyle} role="tablist" aria-label="Enemy families">
                {visibleFamilies.map((family) => renderFamilyTab(family))}
              </div>
            )
          ) : !studioSurface && families.length > 0 ? (
            <div style={{ color: "#d7ba7d", fontSize: 11, marginBottom: 10 }}>
              No enemy families match the current tag filters.
            </div>
          ) : null}
          {studioSurface && registrySubtab === "animated" && selectedEnemyFamily && !data.enemies[selectedEnemyFamily] ? (
            <div style={{ color: STUDIO_INK_MUTED, fontSize: 11, marginBottom: 12 }}>
              No registry entry for <strong style={{ color: STUDIO_INK_SECONDARY }}>{selectedEnemyFamily}</strong>.
            </div>
          ) : null}
          {selectedEnemyFamily && data.enemies[selectedEnemyFamily] ? (
            <>
              {studioSurface ? (
                <StudioEnemyVersionsPanel
                  family={selectedEnemyFamily}
                  versions={data.enemies[selectedEnemyFamily].versions}
                  slotVersionIds={slotVersionIdsByFamily[selectedEnemyFamily] ?? []}
                  activeVersionId={preferredAnimatedVersionIdFromPreview(selectedEnemyFamily, activeGlbUrl)}
                  addSlotDisabled={familyAddSlotDisabled[selectedEnemyFamily] ?? true}
                  addSlotPreparing={addSlotPreparingFamily === selectedEnemyFamily}
                  slotSaveBusy={slotSaveBusyFamily === selectedEnemyFamily}
                  busyKey={busyKey}
                  deleteBusyKey={deleteBusyKey}
                  loadExistingCandidates={loadExistingCandidates}
                  loadExistingSelection={loadExistingSelection}
                  loadExistingBusy={loadExistingBusy}
                  knownTags={tagCatalog}
                  hideDisplayTags={hideDisplayTags}
                  onAddSlot={requestAddSlotModal}
                  onAddEmptySlot={addEmptyEnemySlot}
                  onRemoveSlot={removeEnemySlot}
                  onUpdateSlotVersion={updateEnemySlotVersion}
                  onSaveSlots={saveEnemySlots}
                  onApplyFlags={applyFlags}
                  onPreviewVersion={previewVersion}
                  onDeleteVersion={deleteEnemyVersion}
                  getEnemyDeletePlan={buildEnemyDeletePlan}
                  onPatchTags={patchVersionTags}
                  onLoadExistingSelectionChange={setLoadExistingSelection}
                  onLoadExistingInPreview={openExistingSelection}
                />
              ) : (
                <>
              <RegistryEnemyFamilyPanel
                family={selectedEnemyFamily}
                versions={data.enemies[selectedEnemyFamily].versions}
                slotVersionIds={slotVersionIdsByFamily[selectedEnemyFamily] ?? []}
                addSlotDisabled={familyAddSlotDisabled[selectedEnemyFamily] ?? true}
                addSlotPreparing={addSlotPreparingFamily === selectedEnemyFamily}
                slotSaveBusy={slotSaveBusyFamily === selectedEnemyFamily}
                busyKey={busyKey}
                deleteBusyKey={deleteBusyKey}
                onAddSlot={requestAddSlotModal}
                onAddEmptySlot={addEmptyEnemySlot}
                onRemoveSlot={removeEnemySlot}
                onUpdateSlotVersion={updateEnemySlotVersion}
                onSaveSlots={saveEnemySlots}
                onApplyFlags={applyFlags}
                onPreviewVersion={previewVersion}
                onDeleteVersion={deleteEnemyVersion}
                getEnemyDeletePlan={buildEnemyDeletePlan}
                selectedEnemyVersionKeys={selectedEnemyVersionKeys}
                onToggleEnemyVersionSelect={toggleEnemyVersionSelect}
                onEnemyFamilySelectAllVersions={setEnemyFamilySelectAllVersions}
                bulkEnemyBusy={bulkEnemyBusyFamily === selectedEnemyFamily}
                onBulkEnemySetDraft={(family) => bulkEnemyApplyFlags(family, true, false)}
                onBulkEnemySetInPool={(family) => bulkEnemyApplyFlags(family, false, true)}
                onBulkEnemyDeleteSelected={bulkDeleteEnemyVersions}
                onRenameVersion={renameRegistryVersion}
                knownTags={tagCatalog}
                hideDisplayTags={hideDisplayTags}
                onPatchTags={patchVersionTags}
              />
              <RegistryEnemyLoadExistingSection
                loadExistingCandidates={loadExistingCandidates}
                loadExistingSelection={loadExistingSelection}
                onLoadExistingSelectionChange={setLoadExistingSelection}
                loadExistingBusy={loadExistingBusy}
                onLoadExistingInPreview={openExistingSelection}
                activeFamily={selectedEnemyFamily}
              />
                </>
              )}
            </>
          ) : !studioSurface ? (
            <div style={{ color: "#9d9d9d", fontSize: 11, marginBottom: 12 }}>No enemy families in the registry.</div>
          ) : null}
        </>
      ) : null}

      {registrySubtab === "player" ? (
        studioSurface ? (
          studioPlayerColor ? (
            <StudioPlayerVersionsPanel
              color={studioPlayerColor}
              versions={studioPlayerVersions}
              activeVersionId={preferredPlayerVersionIdFromPreview(studioPlayerColor, activeGlbUrl)}
              pendingVersionId={busyKey}
              knownTags={tagCatalog}
              hideDisplayTags={new Set(["player", studioPlayerColor])}
              scanBusy={playerScanBusy}
              onSelectVersion={(v) => selectAssetByPath(v.path)}
              onApplyFlags={applyPlayerVersionFlags}
              onPatchTags={(v, tags) => patchVersionTags("player", v, tags)}
              onScanExports={() => void scanPlayerExports()}
            />
          ) : (
            <p style={{ color: STUDIO_INK_MUTED, fontSize: 11, margin: 0, lineHeight: 1.5 }}>
              Select a slime color in the Player library to manage versions.
            </p>
          )
        ) : (
          <RegistryPlayerPowerTypesSection
            playerVersions={playerVersions}
            scanBusy={playerScanBusy}
            busyKey={busyKey}
            onScanPlayerExports={scanPlayerExports}
            onApplyFlags={applyPlayerVersionFlags}
            onPreviewVersion={(v) => selectAssetByPath(v.path)}
            onRenameVersion={(v, trimmed) => void renameRegistryVersion("player", v, trimmed)}
            knownTags={tagCatalog}
            hideDisplayTags={new Set(["player"])}
            onPatchTags={(v, tags) => patchVersionTags("player", v, tags)}
          />
        )
      ) : null}

      {registrySubtab === "level" ? (
        <div style={{ color: "#9d9d9d", fontSize: 12, lineHeight: 1.45, marginBottom: 12 }}>
          <p style={{ marginTop: 0 }}>
            Level export registry rows are not available in the manifest yet. This tab will list level assets when the API
            exposes them.
          </p>
        </div>
      ) : null}

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
      {!studioSurface ? (
      <div style={{ marginTop: 16, ...noteStyle }}>
        Persisted to <code style={{ color: "#ce9178" }}>asset_generation/python/model_registry.json</code> via API
        (atomic write; only this manifest path is modified).
      </div>
      ) : null}
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
