import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  fetchEnemyFamilySlots,
  fetchModelRegistry,
  patchRegistryEnemyVersion,
  patchRegistryPlayerActiveVisual,
  putEnemyFamilySlots,
} from "../../api/client";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";

const noteStyle = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };
export const PLAYER_RESTART_REQUIREMENT_COPY =
  "Changes to player model selection are picked up on the next game load/restart. Live hot-reload is not guaranteed.";
export const ENEMY_EMPTY_SLOTS_COPY = "No slots assigned. Runtime falls back to legacy default path for this family.";
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
  const [slotVersionIdsByFamily, setSlotVersionIdsByFamily] = useState<Record<string, string[]>>({});
  const [slotSaveBusyFamily, setSlotSaveBusyFamily] = useState<string | null>(null);

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

  const reload = useCallback(() => {
    setError(null);
    fetchModelRegistry()
      .then(async (registry) => {
        setData(registry);
        await loadEnemySlots(registry);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
      });
  }, [loadEnemySlots]);

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
      setData(updated);
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
      setData(updated);
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
          </tr>
        </thead>
        <tbody>
          {families.map((fam) =>
            data.enemies[fam].versions.map((row) => {
              const key = `${fam}:${row.id}`;
              const pending = busyKey === key;
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
