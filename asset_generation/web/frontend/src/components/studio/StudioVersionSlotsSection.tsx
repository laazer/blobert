import type { CSSProperties } from "react";
import type { RegistryEnemyVersion } from "../../types";
import { canAddEnemySlot } from "../../utils/registrySlotOps";
import { STUDIO_INK_MUTED, STUDIO_INK_SECONDARY, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { ENEMY_EMPTY_SLOTS_COPY } from "../Editor/registryPaneStrings";

function versionOptionLabel(v: RegistryEnemyVersion): string {
  const n = v.name?.trim();
  return n ? `${v.id} — ${n}` : v.id;
}

const selectStyle: CSSProperties = {
  flex: 1,
  minWidth: 0,
  fontSize: 11,
  color: STUDIO_INK_SECONDARY,
  background: "#121218",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 6,
  padding: "6px 8px",
};

const btnStyle: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  fontWeight: 600,
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 6,
  cursor: "pointer",
  background: "#23232e",
  color: STUDIO_INK_SECONDARY,
};

const btnPrimary: CSSProperties = {
  ...btnStyle,
  border: "1px solid color-mix(in srgb, #7c8cf5 50%, transparent)",
  background: "rgba(124,140,245,0.18)",
  color: "#cdd3ff",
};

type Props = {
  family: string;
  versions: RegistryEnemyVersion[];
  slotVersionIds: string[];
  busy: boolean;
  addSlotDisabled: boolean;
  addSlotPreparing: boolean;
  onAddSlot: () => void;
  onAddEmptySlot: () => void;
  onRemoveSlot: (index: number) => void;
  onUpdateSlotVersion: (index: number, versionId: string) => void;
  onSaveSlots: () => void;
};

export function StudioVersionSlotsSection({
  family,
  versions,
  slotVersionIds,
  busy,
  addSlotDisabled,
  addSlotPreparing,
  onAddSlot,
  onAddEmptySlot,
  onRemoveSlot,
  onUpdateSlotVersion,
  onSaveSlots,
}: Props) {
  const validChoices = versions.filter((v) => !v.draft && v.in_use);
  const addDisabled = busy || addSlotDisabled || addSlotPreparing || !canAddEnemySlot(slotVersionIds, versions);

  return (
    <div
      data-testid="studio-version-slots"
      style={{
        marginTop: 4,
        padding: 12,
        borderRadius: 10,
        border: "1px solid rgba(255,255,255,0.04)",
        background: STUDIO_SURFACE_PANEL,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 8,
          flexWrap: "wrap",
          marginBottom: 10,
        }}
      >
        <span style={{ fontSize: 11, fontWeight: 600, color: STUDIO_INK_SECONDARY }}>Spawn pool slots</span>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button
            type="button"
            style={btnStyle}
            disabled={addDisabled}
            data-testid={`registry-add-slot-${family}`}
            title={addSlotPreparing ? "Scanning animated_exports…" : undefined}
            onClick={onAddSlot}
          >
            {addSlotPreparing ? "Scanning…" : "Add slot"}
          </button>
          <button
            type="button"
            style={btnStyle}
            disabled={busy}
            data-testid={`registry-add-empty-slot-${family}`}
            onClick={onAddEmptySlot}
          >
            Empty slot
          </button>
          <button type="button" style={btnPrimary} disabled={busy} onClick={onSaveSlots}>
            Save slots
          </button>
        </div>
      </div>
      {slotVersionIds.length === 0 ? (
        <p style={{ margin: 0, fontSize: 11, color: STUDIO_INK_MUTED, lineHeight: 1.45 }}>{ENEMY_EMPTY_SLOTS_COPY}</p>
      ) : (
        slotVersionIds.map((versionId, idx) => (
          <div
            key={`${family}:slot:${idx}`}
            style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}
          >
            <select
              style={selectStyle}
              disabled={busy}
              value={versionId}
              data-testid={`registry-slot-select-${family}-${idx}`}
              onChange={(e) => onUpdateSlotVersion(idx, e.target.value)}
            >
              <option value="">— Unassigned —</option>
              {validChoices.map((v) => (
                <option key={`${family}:${v.id}`} value={v.id}>
                  {versionOptionLabel(v)}
                </option>
              ))}
            </select>
            <button type="button" style={btnStyle} disabled={busy} onClick={() => onRemoveSlot(idx)}>
              Remove
            </button>
          </div>
        ))
      )}
    </div>
  );
}
