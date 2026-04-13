import type { CSSProperties } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { RegistryEnemyVersion } from "../../types";
import { canAddEnemySlot, nextEnemySlotsAfterRemove } from "../../utils/registrySlotOps";
import {
  addPowerType,
  loadPlayerPowerTypes,
  loadPowerTypeSlots,
  renamePowerType,
  removePowerType,
  savePowerTypeSlots,
  savePlayerPowerTypes,
  type PlayerPowerType,
} from "../../utils/playerPowerTypes";

export const PLAYER_POWER_TYPES_HEADING = "Player power types";

const noteStyle: CSSProperties = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };
const sectionStyle: CSSProperties = { border: "1px solid #3c3c3c", borderRadius: 4, padding: 10, background: "#202020" };
const h3Style: CSSProperties = { marginTop: 0, marginBottom: 8, fontSize: 12, color: "#d4d4d4", fontWeight: 600 };
const subHead: CSSProperties = { fontSize: 11, color: "#b5b5b5", margin: "10px 0 6px", fontWeight: 600 };
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
const th: CSSProperties = { padding: "5px 6px", color: "#9d9d9d", fontWeight: 600, whiteSpace: "nowrap" };
const td: CSSProperties = { padding: "5px 6px", verticalAlign: "middle" };
const radioRow: CSSProperties = { display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" };
const radioLabel: CSSProperties = { display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: "#d4d4d4" };
const nameInputStyle: CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  background: "#252526",
  border: "1px solid #0e639c",
  borderRadius: 3,
  color: "#d4d4d4",
  padding: "2px 6px",
  outline: "none",
};
const nameBtnStyle: CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  background: "none",
  border: "none",
  color: "#d4d4d4",
  cursor: "pointer",
  padding: "2px 0",
  textDecoration: "underline dotted",
  textDecorationColor: "#555",
};

function versionSpawnSelection(row: RegistryEnemyVersion): "draft" | "pool" | null {
  if (row.draft) return "draft";
  if (row.in_use) return "pool";
  return null;
}

function PlayerVersionSelectAllCheckbox({
  allSelected,
  someSelected,
  disabled,
  onChange,
}: {
  allSelected: boolean;
  someSelected: boolean;
  disabled: boolean;
  onChange: (nextChecked: boolean) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.indeterminate = someSelected;
  }, [someSelected]);
  return (
    <input
      ref={ref}
      type="checkbox"
      checked={allSelected}
      disabled={disabled}
      aria-label="Select all player versions"
      data-testid="player-version-select-all"
      onChange={(e) => onChange(e.target.checked)}
    />
  );
}

export type RegistryPlayerPowerTypesSectionProps = {
  playerVersions: RegistryEnemyVersion[];
  scanBusy: boolean;
  busyKey: string | null;
  onScanPlayerExports: () => void;
  onApplyFlags: (v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) => void | Promise<void>;
  onPreviewVersion: (v: RegistryEnemyVersion) => void;
};

export function RegistryPlayerPowerTypesSection({
  playerVersions,
  scanBusy,
  busyKey,
  onScanPlayerExports,
  onApplyFlags,
  onPreviewVersion,
}: RegistryPlayerPowerTypesSectionProps) {
  const [powerTypes, setPowerTypesState] = useState<PlayerPowerType[]>(() => loadPlayerPowerTypes());
  const [sectionSlots, setSectionSlotsState] = useState<Record<string, string[]>>(() => {
    const types = loadPlayerPowerTypes();
    return Object.fromEntries(types.map((pt) => [pt.id, loadPowerTypeSlots(pt.id)]));
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingLabel, setEditingLabel] = useState("");
  const [selectedPlayerVersionIds, setSelectedPlayerVersionIds] = useState<Set<string>>(() => new Set());
  const [playerBulkBusy, setPlayerBulkBusy] = useState(false);

  const setPowerTypes = useCallback((next: PlayerPowerType[]) => {
    savePlayerPowerTypes(next);
    setPowerTypesState(next);
  }, []);

  const updateSlots = useCallback((ptId: string, slots: string[]) => {
    setSectionSlotsState((prev) => ({ ...prev, [ptId]: slots }));
  }, []);

  const handleSaveSlots = useCallback(
    (ptId: string) => {
      savePowerTypeSlots(ptId, sectionSlots[ptId] ?? []);
    },
    [sectionSlots],
  );

  function handleAddSection() {
    const next = addPowerType(powerTypes, `Power Type ${powerTypes.length + 1}`);
    const newPt = next[next.length - 1];
    savePlayerPowerTypes(next);
    setPowerTypesState(next);
    setSectionSlotsState((prev) => ({ ...prev, [newPt.id]: [] }));
    setEditingId(newPt.id);
    setEditingLabel(newPt.label);
  }

  function handleRemoveSection(ptId: string) {
    if (powerTypes.length <= 1) return;
    setPowerTypes(removePowerType(powerTypes, ptId));
    setSectionSlotsState((prev) => {
      const next = { ...prev };
      delete next[ptId];
      return next;
    });
  }

  function handleStartEdit(pt: PlayerPowerType) {
    setEditingId(pt.id);
    setEditingLabel(pt.label);
  }

  function handleSaveEdit(ptId: string) {
    const trimmed = editingLabel.trim();
    if (trimmed) {
      setPowerTypes(renamePowerType(powerTypes, ptId, trimmed));
    }
    setEditingId(null);
    setEditingLabel("");
  }

  function handleCancelEdit() {
    setEditingId(null);
    setEditingLabel("");
  }

  const validChoices = playerVersions.filter((v) => !v.draft && v.in_use);

  useEffect(() => {
    setSelectedPlayerVersionIds((prev) => {
      const next = new Set<string>();
      for (const id of prev) {
        if (playerVersions.some((v) => v.id === id)) next.add(id);
      }
      return next;
    });
  }, [playerVersions]);

  const selectedPlayerCount = playerVersions.filter((v) => selectedPlayerVersionIds.has(v.id)).length;
  const allPlayerSelected =
    playerVersions.length > 0 && selectedPlayerCount === playerVersions.length;
  const somePlayerSelected = selectedPlayerCount > 0 && !allPlayerSelected;

  async function bulkPlayerApplyFlags(nextDraft: boolean, nextInUse: boolean) {
    const ids = [...selectedPlayerVersionIds];
    if (ids.length === 0) return;
    setPlayerBulkBusy(true);
    try {
      for (const id of ids) {
        const row = playerVersions.find((v) => v.id === id);
        if (!row) continue;
        await onApplyFlags(row, nextDraft, nextInUse);
      }
      setSelectedPlayerVersionIds(new Set());
    } finally {
      setPlayerBulkBusy(false);
    }
  }

  return (
    <div style={{ ...sectionStyle, marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h3 style={h3Style}>{PLAYER_POWER_TYPES_HEADING}</h3>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            type="button"
            style={btnSecondary}
            disabled={scanBusy}
            data-testid="player-scan-exports"
            onClick={onScanPlayerExports}
          >
            {scanBusy ? "Scanning…" : "Scan player exports"}
          </button>
          <button
            type="button"
            style={btnSecondary}
            data-testid="player-add-power-type"
            onClick={handleAddSection}
          >
            Add power type
          </button>
        </div>
      </div>
      <div style={noteStyle}>
        <strong>Slots</strong> are the ordered active pool per power type (saved locally).{" "}
        <strong>Draft</strong> versions are not slottable.{" "}
        <strong>In pool</strong> versions are active. Click a section name to rename it.
      </div>

      {powerTypes.map((pt) => {
        const slots = sectionSlots[pt.id] ?? [];
        const addDisabled = !canAddEnemySlot(slots, playerVersions);

        return (
          <div
            key={pt.id}
            style={{ border: "1px solid #2d2d2d", borderRadius: 4, padding: 8, marginBottom: 12 }}
          >
            <div
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}
            >
              {editingId === pt.id ? (
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    style={nameInputStyle}
                    value={editingLabel}
                    autoFocus
                    data-testid={`player-pt-name-input-${pt.id}`}
                    onChange={(e) => setEditingLabel(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveEdit(pt.id);
                      if (e.key === "Escape") handleCancelEdit();
                    }}
                  />
                  <button type="button" style={btnSecondary} onClick={() => handleSaveEdit(pt.id)}>
                    Save
                  </button>
                  <button type="button" style={btnSecondary} onClick={handleCancelEdit}>
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  style={nameBtnStyle}
                  title="Click to rename"
                  data-testid={`player-pt-name-btn-${pt.id}`}
                  onClick={() => handleStartEdit(pt)}
                >
                  {pt.label}
                </button>
              )}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  style={btnSecondary}
                  disabled={addDisabled}
                  title="Append an unassigned slot row"
                  data-testid={`player-pt-add-slot-${pt.id}`}
                  onClick={() => updateSlots(pt.id, [...slots, ""])}
                >
                  Add slot
                </button>
                <button
                  type="button"
                  style={btnPrimary}
                  data-testid={`player-pt-save-slots-${pt.id}`}
                  onClick={() => handleSaveSlots(pt.id)}
                >
                  Save slots
                </button>
                {powerTypes.length > 1 && (
                  <button
                    type="button"
                    style={btnSecondary}
                    data-testid={`player-pt-remove-${pt.id}`}
                    onClick={() => handleRemoveSection(pt.id)}
                  >
                    Remove section
                  </button>
                )}
              </div>
            </div>

            <div style={subHead}>Slots</div>
            {slots.length === 0 ? (
              <div style={{ color: "#d7ba7d", fontSize: 11, marginBottom: 10 }}>
                No slots configured. Add a slot and assign a version.
              </div>
            ) : (
              slots.map((versionId, idx) => (
                <div
                  key={`${pt.id}:slot:${idx}`}
                  style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}
                >
                  <select
                    style={selectStyle}
                    value={versionId}
                    data-testid={`player-pt-slot-select-${pt.id}-${idx}`}
                    onChange={(e) => {
                      const next = [...slots];
                      next[idx] = e.target.value;
                      updateSlots(pt.id, next);
                    }}
                  >
                    <option value="">— Unassigned —</option>
                    {validChoices.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.id}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    style={btnSecondary}
                    onClick={() => updateSlots(pt.id, nextEnemySlotsAfterRemove(slots, idx))}
                  >
                    Remove
                  </button>
                </div>
              ))
            )}
          </div>
        );
      })}

      <div style={{ ...subHead, marginTop: 16 }}>All versions</div>
      <div style={noteStyle}>
        Select multiple rows to <strong>Set selected → Draft</strong> or <strong>In pool</strong> in one pass.
      </div>
      {playerVersions.length === 0 ? (
        <div style={{ color: "#9d9d9d", fontSize: 11 }}>
          No player versions registered. Use &ldquo;Scan player exports&rdquo; to detect{" "}
          <code style={{ color: "#ce9178" }}>player_exports/*.glb</code> files.
        </div>
      ) : (
        <>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            <span style={{ fontSize: 10, color: "#888" }}>Selected:</span>
            <button
              type="button"
              style={btnSecondary}
              disabled={playerBulkBusy || selectedPlayerCount === 0}
              data-testid="player-version-bulk-draft"
              onClick={() => void bulkPlayerApplyFlags(true, false)}
            >
              Set selected → Draft
            </button>
            <button
              type="button"
              style={btnSecondary}
              disabled={playerBulkBusy || selectedPlayerCount === 0}
              data-testid="player-version-bulk-pool"
              onClick={() => void bulkPlayerApplyFlags(false, true)}
            >
              Set selected → In pool
            </button>
          </div>
          <div style={{ overflowX: "auto", width: "100%" }}>
            <table style={{ width: "100%", minWidth: 480, borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #3c3c3c" }}>
                  <th style={{ ...th, width: 36 }}>
                    <PlayerVersionSelectAllCheckbox
                      allSelected={allPlayerSelected}
                      someSelected={somePlayerSelected}
                      disabled={playerBulkBusy}
                      onChange={(checked) =>
                        setSelectedPlayerVersionIds(
                          checked ? new Set(playerVersions.map((v) => v.id)) : new Set(),
                        )
                      }
                    />
                  </th>
                  <th style={th}>Version id</th>
                  <th style={{ ...th, maxWidth: 180 }}>Path</th>
                  <th style={th}>Spawn state</th>
                  <th style={th}>Preview</th>
                </tr>
              </thead>
              <tbody>
                {playerVersions.map((row) => {
                  const key = `player:${row.id}`;
                  const pending = busyKey === key || playerBulkBusy;
                  const selected = versionSpawnSelection(row);
                  return (
                    <tr key={key} style={{ borderBottom: "1px solid #2d2d2d" }}>
                      <td style={td}>
                        <input
                          type="checkbox"
                          checked={selectedPlayerVersionIds.has(row.id)}
                          disabled={pending}
                          aria-label={`Select ${row.id}`}
                          data-testid={`player-version-select-${row.id}`}
                          onChange={() => {
                            setSelectedPlayerVersionIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(row.id)) next.delete(row.id);
                              else next.add(row.id);
                              return next;
                            });
                          }}
                        />
                      </td>
                      <td style={td}>{row.id}</td>
                      <td
                        style={{
                          ...td,
                          maxWidth: 180,
                          wordBreak: "break-all",
                          fontSize: 10,
                          color: "#9d9d9d",
                        }}
                      >
                        {row.path}
                      </td>
                      <td style={td}>
                        <div
                          role="radiogroup"
                          aria-label={`Spawn state for ${row.id}`}
                          style={radioRow}
                          data-testid={`player-version-spawn-${row.id}`}
                        >
                          {(
                            [
                              ["draft", "Draft"],
                              ["pool", "In pool"],
                            ] as const
                          ).map(([value, label]) => (
                            <label key={value} style={radioLabel}>
                              <input
                                type="radio"
                                name={`player-spawn-${row.id}`}
                                value={value}
                                checked={selected === value}
                                disabled={pending}
                                data-testid={`player-version-spawn-${row.id}-${value}`}
                                onChange={() => {
                                  if (value === "draft") void onApplyFlags(row, true, false);
                                  else void onApplyFlags(row, false, true);
                                }}
                              />
                              <span>{label}</span>
                            </label>
                          ))}
                        </div>
                      </td>
                      <td style={td}>
                        <button
                          type="button"
                          style={btnSecondary}
                          disabled={pending}
                          title={`Load ${row.id} into the 3D preview`}
                          onClick={() => onPreviewVersion(row)}
                        >
                          Preview
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
