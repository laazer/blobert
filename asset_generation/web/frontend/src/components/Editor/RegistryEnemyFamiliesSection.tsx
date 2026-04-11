import type { CSSProperties } from "react";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import type { EnemyDeletePlan } from "./registryEnemyTypes";
import { ENEMY_EMPTY_SLOTS_COPY } from "./registryPaneStrings";

const noteStyle: CSSProperties = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };
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
const th: CSSProperties = { padding: "6px 8px", color: "#9d9d9d", fontWeight: 600 };
const td: CSSProperties = { padding: "6px 8px", verticalAlign: "middle" };
const subHead: CSSProperties = { fontSize: 11, color: "#b5b5b5", margin: "10px 0 6px", fontWeight: 600 };
const radioRow: CSSProperties = { display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" };
const radioLabel: CSSProperties = { display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: "#d4d4d4" };

/** Draft vs spawn pool: non-draft rows can still be out of the pool (``in_use: false``); those must not show as pool or clicks are a no-op. */
function enemyVersionSpawnSelection(row: RegistryEnemyVersion): "draft" | "pool" | null {
  if (row.draft) return "draft";
  if (row.in_use) return "pool";
  return null;
}

function versionOptionLabel(v: RegistryEnemyVersion): string {
  const n = v.name?.trim();
  return n ? `${v.id} — ${n}` : v.id;
}

export type RegistryEnemyFamiliesSectionProps = {
  families: string[];
  enemies: ModelRegistryPayload["enemies"];
  slotVersionIdsByFamily: Record<string, string[]>;
  /** True when every slottable version is already listed (or none exist). */
  familyAddSlotDisabled: Record<string, boolean>;
  /** Family currently running POST sync_animated_exports before the add-slot modal opens. */
  addSlotPreparingFamily: string | null;
  slotSaveBusyFamily: string | null;
  busyKey: string | null;
  deleteBusyKey: string | null;
  onAddSlot: (family: string) => void;
  onAddEmptySlot: (family: string) => void;
  onRemoveSlot: (family: string, index: number) => void;
  onUpdateSlotVersion: (family: string, index: number, versionId: string) => void;
  onSaveSlots: (family: string) => void;
  onApplyFlags: (family: string, v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) => void;
  onDeleteVersion: (family: string, v: RegistryEnemyVersion) => void;
  getEnemyDeletePlan: (family: string, v: RegistryEnemyVersion) => EnemyDeletePlan | null;
};

export function RegistryEnemyFamiliesSection({
  families,
  enemies,
  slotVersionIdsByFamily,
  familyAddSlotDisabled,
  addSlotPreparingFamily,
  slotSaveBusyFamily,
  busyKey,
  deleteBusyKey,
  onAddSlot,
  onAddEmptySlot,
  onRemoveSlot,
  onUpdateSlotVersion,
  onSaveSlots,
  onApplyFlags,
  onDeleteVersion,
  getEnemyDeletePlan,
}: RegistryEnemyFamiliesSectionProps) {
  return (
    <div style={{ ...sectionStyle, marginBottom: 16 }}>
      <h3 style={h3Style}>Enemy version slots &amp; versions</h3>
      <div style={noteStyle}>
        <strong>Slots</strong> are the runtime spawn pool per family (order is saved per family).{" "}
        <strong>Versions</strong> lists every registered row: <strong>Draft</strong> vs <strong>In pool</strong> and delete
        apply to the manifest immediately (separate from Save Slots).
      </div>
      <div style={noteStyle}>
        <strong>Draft</strong> versions are not slottable until you switch them to <strong>In pool</strong>. Use slots to
        order which in-pool variants spawn.
      </div>
      <div style={noteStyle}>
        <strong>Add slot</strong> first scans <code style={{ color: "#ce9178" }}>animated_exports/</code> for{" "}
        <code style={{ color: "#ce9178" }}>{`{family}_animated_*.glb`}</code> files on disk and registers any missing
        variants in the manifest (then you pick which version to append to the slot list).{" "}
        <strong>Add empty slot</strong> appends an unassigned row (pick a version later, then Save slots).
      </div>

      {families.map((family) => {
        const versions = enemies[family].versions;
        const validChoices = versions.filter((v) => !v.draft && v.in_use);
        const slotRows = slotVersionIdsByFamily[family] ?? [];
        const busy = slotSaveBusyFamily === family;
        const addDisabled = familyAddSlotDisabled[family] ?? true;
        const preparing = addSlotPreparingFamily === family;

        return (
          <div key={`enemy-family:${family}`} style={{ border: "1px solid #2d2d2d", borderRadius: 4, padding: 8, marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <strong style={{ fontSize: 13 }}>{family}</strong>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  style={btnSecondary}
                  disabled={busy || addDisabled || preparing}
                  title={
                    preparing
                      ? "Scanning animated_exports for GLB files not yet in the registry…"
                      : undefined
                  }
                  data-testid={`registry-add-slot-${family}`}
                  onClick={() => onAddSlot(family)}
                >
                  {preparing ? "Scanning…" : "Add slot"}
                </button>
                <button
                  type="button"
                  style={btnSecondary}
                  disabled={busy}
                  title="Append an unassigned slot (assign a version in the dropdown, then Save slots)"
                  data-testid={`registry-add-empty-slot-${family}`}
                  onClick={() => onAddEmptySlot(family)}
                >
                  Add empty slot
                </button>
                <button type="button" style={btnPrimary} disabled={busy} onClick={() => onSaveSlots(family)}>
                  Save slots
                </button>
              </div>
            </div>

            <div style={subHead}>Spawn slots</div>
            {slotRows.length === 0 ? (
              <div style={{ color: "#d7ba7d", fontSize: 11, marginBottom: 10 }}>{ENEMY_EMPTY_SLOTS_COPY}</div>
            ) : (
              slotRows.map((versionId, idx) => (
                <div key={`${family}:slot:${idx}`} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                  <select
                    style={selectStyle}
                    disabled={busy}
                    value={versionId}
                    onChange={(e) => onUpdateSlotVersion(family, idx, e.target.value)}
                  >
                    <option value="">— Unassigned —</option>
                    {validChoices.map((v) => (
                      <option key={`${family}:${v.id}`} value={v.id}>
                        {versionOptionLabel(v)}
                      </option>
                    ))}
                  </select>
                  <button type="button" style={btnSecondary} disabled={busy} onClick={() => onRemoveSlot(family, idx)}>
                    Remove
                  </button>
                </div>
              ))
            )}

            <div style={subHead}>All versions</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #3c3c3c" }}>
                  <th style={th}>Version id</th>
                  <th style={th}>Name</th>
                  <th style={th}>Path</th>
                  <th style={th}>Spawn state</th>
                  <th style={th}>Delete</th>
                </tr>
              </thead>
              <tbody>
                {versions.map((row) => {
                  const key = `${family}:${row.id}`;
                  const pending = busyKey === key || deleteBusyKey === key;
                  const deletePlan = getEnemyDeletePlan(family, row);
                  return (
                    <tr key={key} style={{ borderBottom: "1px solid #2d2d2d" }}>
                      <td style={td}>{row.id}</td>
                      <td style={td}>{row.name?.trim() ? row.name.trim() : "—"}</td>
                      <td style={{ ...td, wordBreak: "break-all" }}>{row.path}</td>
                      <td style={td}>
                        <div
                          role="radiogroup"
                          aria-label={`Spawn state for ${row.id}`}
                          style={radioRow}
                          data-testid={`registry-enemy-spawn-${family}-${row.id}`}
                        >
                          {(
                            [
                              ["draft", "Draft"],
                              ["pool", "In pool"],
                            ] as const
                          ).map(([value, label]) => {
                            const selected = enemyVersionSpawnSelection(row);
                            return (
                              <label key={value} style={radioLabel}>
                                <input
                                  type="radio"
                                  name={`enemy-spawn-${family}-${row.id}`}
                                  value={value}
                                  checked={selected === value}
                                  disabled={pending}
                                  data-testid={`registry-enemy-spawn-${family}-${row.id}-${value}`}
                                  onChange={() => {
                                    if (value === "draft") onApplyFlags(family, row, true, false);
                                    else onApplyFlags(family, row, false, true);
                                  }}
                                />
                                <span>{label}</span>
                              </label>
                            );
                          })}
                        </div>
                      </td>
                      <td style={td}>
                        <button
                          type="button"
                          style={btnSecondary}
                          disabled={pending || !deletePlan}
                          onClick={() => onDeleteVersion(family, row)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}
