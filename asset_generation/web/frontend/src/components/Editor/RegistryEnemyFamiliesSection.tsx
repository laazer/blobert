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

function versionOptionLabel(v: RegistryEnemyVersion): string {
  const n = v.name?.trim();
  return n ? `${v.id} — ${n}` : v.id;
}

export type RegistryEnemyFamiliesSectionProps = {
  families: string[];
  enemies: ModelRegistryPayload["enemies"];
  slotVersionIdsByFamily: Record<string, string[]>;
  slotSaveBusyFamily: string | null;
  busyKey: string | null;
  deleteBusyKey: string | null;
  onAddSlot: (family: string) => void;
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
  slotSaveBusyFamily,
  busyKey,
  deleteBusyKey,
  onAddSlot,
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
        <strong>Versions</strong> lists every registered row: draft / in-use flags and delete apply to the manifest
        immediately (separate from Save Slots).
      </div>
      <div style={noteStyle}>
        <strong>Draft</strong> exports stay off the default spawn pool until promoted. <strong>In pool</strong> is off
        while draft is on.
      </div>

      {families.map((family) => {
        const versions = enemies[family].versions;
        const validChoices = versions.filter((v) => !v.draft && v.in_use);
        const slotRows = slotVersionIdsByFamily[family] ?? [];
        const busy = slotSaveBusyFamily === family;

        return (
          <div key={`enemy-family:${family}`} style={{ border: "1px solid #2d2d2d", borderRadius: 4, padding: 8, marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <strong style={{ fontSize: 13 }}>{family}</strong>
              <div style={{ display: "flex", gap: 8 }}>
                <button type="button" style={btnSecondary} disabled={busy || validChoices.length === 0} onClick={() => onAddSlot(family)}>
                  Add slot
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
                  <th style={th}>Draft</th>
                  <th style={th}>In pool</th>
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
                        <input
                          type="checkbox"
                          checked={row.draft}
                          disabled={pending}
                          onChange={(e) => {
                            const d = e.target.checked;
                            onApplyFlags(family, row, d, d ? false : row.in_use);
                          }}
                        />
                      </td>
                      <td style={td}>
                        <input
                          type="checkbox"
                          checked={row.in_use && !row.draft}
                          disabled={pending || row.draft}
                          onChange={(e) => {
                            onApplyFlags(family, row, row.draft, e.target.checked);
                          }}
                        />
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
