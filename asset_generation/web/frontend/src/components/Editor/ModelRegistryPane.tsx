import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  deleteRegistryEnemyVersion,
  fetchLoadExistingCandidates,
  fetchEnemyFamilySlots,
  fetchModelRegistry,
  openExistingRegistryModel,
  patchRegistryEnemyVersion,
  patchRegistryPlayerActiveVisual,
  putEnemyFamilySlots,
  type LoadExistingCandidate,
  type OpenExistingRegistryModelRequest,
  type DeleteEnemyVersionRequest,
} from "../../api/client";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";

const noteStyle = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };
export const PLAYER_RESTART_REQUIREMENT_COPY =
  "Changes to player model selection are picked up on the next game load/restart. Live hot-reload is not guaranteed.";
export const ENEMY_EMPTY_SLOTS_COPY = "No slots assigned. Runtime falls back to legacy default path for this family.";
export const LOAD_EXISTING_EMPTY_COPY = "No draft or in-use registry models available.";
export const DRAFT_DELETE_CONFIRM_COPY =
  "Confirm irreversible draft delete. This removes the registry row and may also delete the draft file when file deletion is enabled.";
export const IN_USE_DELETE_CONFIRM_COPY =
  "Deleting an in-use version affects spawn eligibility and may be rejected by safety guards (for example: sole in-use version).";

export type EnemyDeletePlan = {
  confirmMessage: string;
  request: DeleteEnemyVersionRequest;
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

export function loadExistingCandidateKey(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `enemy:${row.family}:${row.version_id}`;
  }
  return `player:${row.path}`;
}

export function loadExistingCandidateLabel(row: LoadExistingCandidate): string {
  if (row.kind === "enemy") {
    return `${row.family}/${row.version_id} (${row.path})`;
  }
  return `player_active_visual (${row.path})`;
}

export function toOpenExistingRequest(row: LoadExistingCandidate): OpenExistingRegistryModelRequest {
  if (row.kind === "enemy") {
    return { kind: "enemy", family: row.family, version_id: row.version_id };
  }
  return { kind: "path", path: row.path };
}

export function nextEnemySlotsAfterAdd(
  current: string[],
  candidates: Pick<RegistryEnemyVersion, "id" | "draft" | "in_use">[],
): string[] {
  const firstAvailable = candidates.find((v) => !v.draft && v.in_use && !current.includes(v.id));
  if (!firstAvailable) return current;
  return [...current, firstAvailable.id];
}

export function nextEnemySlotsAfterRemove(current: string[], index: number): string[] {
  const next = [...current];
  next.splice(index, 1);
  return next;
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
  const [lastOpenedExistingPath, setLastOpenedExistingPath] = useState<string | null>(null);

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

  function addEnemySlot(family: string) {
    const candidates = data?.enemies[family]?.versions ?? [];
    const draft = slotVersionIdsByFamily[family] ?? [];
    const next = nextEnemySlotsAfterAdd(draft, candidates);
    if (next === draft) return;
    setSlotVersionIdsByFamily((prev) => ({
      ...prev,
      [family]: next,
    }));
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
      setLastOpenedExistingPath(payload.path);
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

  const families = useMemo(() => Object.keys(data.enemies).sort(), [data.enemies]);
  const playerCandidates = useMemo(() => {
    const rows: { family: string; id: string; path: string }[] = [];
    for (const family of families) {
      for (const version of data.enemies[family].versions) {
        if (!version.draft && version.path.endsWith(".glb")) {
          rows.push({ family, id: version.id, path: version.path });
        }
      }
    }
    return rows;
  }, [data.enemies, families]);
  const playerBusy = busyKey === "player_active_visual";

  return (
    <div style={{ padding: 12, color: "#d4d4d4", fontSize: 12, overflow: "auto", flex: 1 }}>
      <div style={{ ...sectionStyle, marginBottom: 16 }}>
        <h3 style={h3Style}>Player Active Visual</h3>
        <div style={noteStyle}>{PLAYER_RESTART_REQUIREMENT_COPY}</div>
        <label style={{ display: "block", marginBottom: 6, color: "#9d9d9d" }} htmlFor="player-active-visual-select">
          Active player model
        </label>
        <select
          id="player-active-visual-select"
          style={selectStyle}
          disabled={playerBusy}
          value={data.player_active_visual?.path ?? ""}
          onChange={(e) => {
            if (!e.target.value) return;
            applyPlayerSelection(e.target.value);
          }}
        >
          <option value="" disabled>
            Select a non-draft .glb
          </option>
          {playerCandidates.map((row) => (
            <option key={`${row.family}:${row.id}`} value={row.path}>
              {row.path}
            </option>
          ))}
        </select>
      </div>

      <div style={{ ...sectionStyle, marginBottom: 16 }}>
        <h3 style={h3Style}>Load / Open Existing</h3>
        <div style={noteStyle}>
          This picker is registry-backed only. Arbitrary OS paths and free-form <code>res://</code> entries are not accepted.
        </div>
        {loadExistingCandidates.length === 0 ? (
          <div style={{ color: "#d7ba7d", fontSize: 11 }}>{LOAD_EXISTING_EMPTY_COPY}</div>
        ) : (
          <>
            <label style={{ display: "block", marginBottom: 6, color: "#9d9d9d" }} htmlFor="load-existing-select">
              Existing model
            </label>
            <select
              id="load-existing-select"
              style={selectStyle}
              disabled={loadExistingBusy}
              value={loadExistingSelection}
              onChange={(e) => setLoadExistingSelection(e.target.value)}
            >
              {loadExistingCandidates.map((row) => (
                <option key={loadExistingCandidateKey(row)} value={loadExistingCandidateKey(row)}>
                  {loadExistingCandidateLabel(row)}
                </option>
              ))}
            </select>
            <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
              <button
                type="button"
                style={btnPrimary}
                disabled={loadExistingBusy || !loadExistingSelection}
                onClick={openExistingSelection}
              >
                Open Selected
              </button>
              {lastOpenedExistingPath ? (
                <span style={{ color: "#9d9d9d", fontSize: 11 }}>Resolved: {lastOpenedExistingPath}</span>
              ) : null}
            </div>
          </>
        )}
      </div>

      <div style={{ ...sectionStyle, marginBottom: 16 }}>
        <h3 style={h3Style}>Enemy Version Slots</h3>
        <div style={noteStyle}>
          Slots are the runtime spawn pool per family. Add/remove rows, then save full replacement order for each
          family.
        </div>
        {families.map((family) => {
          const versions = data.enemies[family].versions;
          const validChoices = versions.filter((v) => !v.draft && v.in_use);
          const slotRows = slotVersionIdsByFamily[family] ?? [];
          const busy = slotSaveBusyFamily === family;
          return (
            <div key={`slots:${family}`} style={{ border: "1px solid #2d2d2d", borderRadius: 4, padding: 8, marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <strong>{family}</strong>
                <div style={{ display: "flex", gap: 8 }}>
                  <button type="button" style={btnSecondary} disabled={busy || validChoices.length === 0} onClick={() => addEnemySlot(family)}>
                    Add Slot
                  </button>
                  <button type="button" style={btnPrimary} disabled={busy} onClick={() => saveEnemySlots(family)}>
                    Save Slots
                  </button>
                </div>
              </div>
              {slotRows.length === 0 ? (
                <div style={{ color: "#d7ba7d", fontSize: 11 }}>{ENEMY_EMPTY_SLOTS_COPY}</div>
              ) : (
                slotRows.map((versionId, idx) => (
                  <div key={`${family}:slot:${idx}`} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                    <select
                      style={selectStyle}
                      disabled={busy}
                      value={versionId}
                      onChange={(e) => updateEnemySlotVersion(family, idx, e.target.value)}
                    >
                      {validChoices.map((v) => (
                        <option key={`${family}:${v.id}`} value={v.id}>
                          {v.id}
                        </option>
                      ))}
                    </select>
                    <button type="button" style={btnSecondary} disabled={busy} onClick={() => removeEnemySlot(family, idx)}>
                      Remove
                    </button>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>

      <div style={noteStyle}>
        <strong>Draft</strong> exports are excluded from the default spawn pool until promoted (MRVC-4).
        <strong> Demotion:</strong> mark <strong>Draft</strong> — the version leaves the in-use pool but stays on disk.
      </div>
      {error && (
        <div style={{ color: "#f14c4c", marginBottom: 8, fontSize: 11 }}>{error}</div>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #3c3c3c" }}>
            <th style={th}>Family</th>
            <th style={th}>Version id</th>
            <th style={th}>Path</th>
            <th style={th}>Draft</th>
            <th style={th}>In pool</th>
            <th style={th}>Delete</th>
          </tr>
        </thead>
        <tbody>
          {families.map((fam) =>
            data.enemies[fam].versions.map((row) => {
              const key = `${fam}:${row.id}`;
              const pending = busyKey === key || deleteBusyKey === key;
              const deletePlan = buildEnemyDeletePlan(fam, row);
              return (
                <tr key={key} style={{ borderBottom: "1px solid #2d2d2d" }}>
                  <td style={td}>{fam}</td>
                  <td style={td}>{row.id}</td>
                  <td style={{ ...td, wordBreak: "break-all" }}>{row.path}</td>
                  <td style={td}>
                    <input
                      type="checkbox"
                      checked={row.draft}
                      disabled={pending}
                      onChange={(e) => {
                        const d = e.target.checked;
                        applyFlags(fam, row, d, d ? false : row.in_use);
                      }}
                    />
                  </td>
                  <td style={td}>
                    <input
                      type="checkbox"
                      checked={row.in_use && !row.draft}
                      disabled={pending || row.draft}
                      onChange={(e) => {
                        applyFlags(fam, row, row.draft, e.target.checked);
                      }}
                    />
                  </td>
                  <td style={td}>
                    <button
                      type="button"
                      style={btnSecondary}
                      disabled={pending || !deletePlan}
                      onClick={() => deleteEnemyVersion(fam, row)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              );
            }),
          )}
        </tbody>
      </table>
      <div style={{ marginTop: 16, ...noteStyle }}>
        Persisted to <code style={{ color: "#ce9178" }}>asset_generation/python/model_registry.json</code> via API
        (atomic write; only this manifest path is modified).
      </div>
    </div>
  );
}

const th: CSSProperties = { padding: "6px 8px", color: "#9d9d9d", fontWeight: 600 };
const td: CSSProperties = { padding: "6px 8px", verticalAlign: "middle" };
const sectionStyle: CSSProperties = { border: "1px solid #3c3c3c", borderRadius: 4, padding: 10, background: "#202020" };
const h3Style: CSSProperties = { marginTop: 0, marginBottom: 8, fontSize: 12, color: "#d4d4d4", fontWeight: 600 };
const selectStyle: CSSProperties = {
  width: "100%",
  maxWidth: 480,
  fontSize: 11,
  color: "#d4d4d4",
  background: "#252526",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "4px 6px",
};
const btnSecondary: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
const btnPrimary: CSSProperties = {
  ...btnSecondary,
  border: "1px solid #0e639c",
  background: "#0e639c",
};
