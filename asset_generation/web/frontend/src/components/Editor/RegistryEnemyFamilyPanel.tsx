import { useEffect, useRef, useState, type CSSProperties } from "react";
import type { RegistryEnemyVersion } from "../../types";
import { registryFamilyTabLabel } from "../../utils/registryFamilyNav";
import { enemyRegistryRowKey } from "../../utils/registryVersionSelection";
import type { EnemyDeletePlan } from "./registryEnemyTypes";
import { ENEMY_EMPTY_SLOTS_COPY, ENEMY_VERSIONS_HELP_PARAGRAPHS, ENEMY_VERSIONS_SECTION_HEADING } from "./registryPaneStrings";
import { RegistryInfoButton } from "./RegistryHelpDialog";
import { RegistryTagEditor } from "./RegistryTagEditor";
import { RegistryVersionNameInput } from "./RegistryVersionNameInput";

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
const th: CSSProperties = { padding: "5px 6px", color: "#9d9d9d", fontWeight: 600, whiteSpace: "nowrap" };
const td: CSSProperties = { padding: "5px 6px", verticalAlign: "middle" };
const subHead: CSSProperties = { fontSize: 11, color: "#b5b5b5", margin: "10px 0 6px", fontWeight: 600 };
const radioRow: CSSProperties = { display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" };
const radioLabel: CSSProperties = { display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: "#d4d4d4" };
const helpParagraph: CSSProperties = { margin: "0 0 8px" };

function enemyVersionSpawnSelection(row: RegistryEnemyVersion): "draft" | "pool" | null {
  if (row.draft) return "draft";
  if (row.in_use) return "pool";
  return null;
}

function versionOptionLabel(v: RegistryEnemyVersion): string {
  const n = v.name?.trim();
  return n ? `${v.id} — ${n}` : v.id;
}

function FamilyVersionSelectAllCheckbox({
  family,
  allSelected,
  someSelected,
  disabled,
  onChange,
}: {
  family: string;
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
      aria-label={`Select all versions for ${family}`}
      data-testid={`registry-enemy-select-all-${family}`}
      onChange={(e) => onChange(e.target.checked)}
    />
  );
}

export type RegistryEnemyFamilyPanelProps = {
  family: string;
  versions: RegistryEnemyVersion[];
  slotVersionIds: string[];
  addSlotDisabled: boolean;
  addSlotPreparing: boolean;
  slotSaveBusy: boolean;
  busyKey: string | null;
  deleteBusyKey: string | null;
  onAddSlot: (family: string) => void;
  onAddEmptySlot: (family: string) => void;
  onRemoveSlot: (family: string, index: number) => void;
  onUpdateSlotVersion: (family: string, index: number, versionId: string) => void;
  onSaveSlots: (family: string) => void;
  onApplyFlags: (family: string, v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) => void;
  onPreviewVersion: (family: string, v: RegistryEnemyVersion) => void;
  onDeleteVersion: (family: string, v: RegistryEnemyVersion) => void;
  getEnemyDeletePlan: (family: string, v: RegistryEnemyVersion) => EnemyDeletePlan | null;
  selectedEnemyVersionKeys: ReadonlySet<string>;
  onToggleEnemyVersionSelect: (family: string, versionId: string) => void;
  onEnemyFamilySelectAllVersions: (family: string, nextChecked: boolean) => void;
  bulkEnemyBusy: boolean;
  onBulkEnemySetDraft: (family: string) => void;
  onBulkEnemySetInPool: (family: string) => void;
  onBulkEnemyDeleteSelected: (family: string) => void;
  onRenameVersion: (family: string, v: RegistryEnemyVersion, trimmedDisplayName: string) => void | Promise<void>;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  onPatchTags: (family: string, v: RegistryEnemyVersion, tags: string[]) => void | Promise<void>;
};

export function RegistryEnemyFamilyPanel({
  family,
  versions,
  slotVersionIds,
  addSlotDisabled,
  addSlotPreparing,
  slotSaveBusy,
  busyKey,
  deleteBusyKey,
  onAddSlot,
  onAddEmptySlot,
  onRemoveSlot,
  onUpdateSlotVersion,
  onSaveSlots,
  onApplyFlags,
  onPreviewVersion,
  onDeleteVersion,
  getEnemyDeletePlan,
  selectedEnemyVersionKeys,
  onToggleEnemyVersionSelect,
  onEnemyFamilySelectAllVersions,
  bulkEnemyBusy,
  onBulkEnemySetDraft,
  onBulkEnemySetInPool,
  onBulkEnemyDeleteSelected,
  onRenameVersion,
  knownTags,
  hideDisplayTags,
  onPatchTags,
}: RegistryEnemyFamilyPanelProps) {
  const [helpOpen, setHelpOpen] = useState(false);

  const validChoices = versions.filter((v) => !v.draft && v.in_use);
  const busy = slotSaveBusy;
  const selectedInFamily = versions.filter((v) =>
    selectedEnemyVersionKeys.has(enemyRegistryRowKey(family, v.id)),
  ).length;
  const allSelected = versions.length > 0 && selectedInFamily === versions.length;
  const someSelected = selectedInFamily > 0 && !allSelected;

  return (
    <div style={{ ...sectionStyle, marginBottom: 16 }} data-testid={`registry-enemy-family-panel-${family}`}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
        <h3 style={{ ...h3Style, marginBottom: 0, flex: "1 1 auto" }}>{ENEMY_VERSIONS_SECTION_HEADING}</h3>
        <RegistryInfoButton
          aria-label="How enemy slots and versions work"
          title="How enemy slots and versions work"
          dialogTitle={ENEMY_VERSIONS_SECTION_HEADING}
          open={helpOpen}
          onOpen={() => setHelpOpen(true)}
          onClose={() => setHelpOpen(false)}
        >
          {ENEMY_VERSIONS_HELP_PARAGRAPHS.map((text, i) => (
            <p key={i} style={helpParagraph}>
              {text}
            </p>
          ))}
        </RegistryInfoButton>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
        <strong style={{ fontSize: 13 }} data-testid={`registry-enemy-family-title-${family}`}>
          {registryFamilyTabLabel(family)}
        </strong>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            type="button"
            style={btnSecondary}
            disabled={busy || addSlotDisabled || addSlotPreparing}
            title={
              addSlotPreparing
                ? "Scanning animated_exports for GLB files not yet in the registry…"
                : undefined
            }
            data-testid={`registry-add-slot-${family}`}
            onClick={() => onAddSlot(family)}
          >
            {addSlotPreparing ? "Scanning…" : "Add slot"}
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
      {slotVersionIds.length === 0 ? (
        <div style={{ color: "#d7ba7d", fontSize: 11, marginBottom: 10 }}>{ENEMY_EMPTY_SLOTS_COPY}</div>
      ) : (
        slotVersionIds.map((versionId, idx) => (
          <div key={`${family}:slot:${idx}`} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
            <select
              style={selectStyle}
              disabled={busy}
              value={versionId}
              data-testid={`registry-slot-select-${family}-${idx}`}
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
          disabled={busy || bulkEnemyBusy || selectedInFamily === 0}
          data-testid={`registry-enemy-bulk-draft-${family}`}
          onClick={() => onBulkEnemySetDraft(family)}
        >
          Set selected → Draft
        </button>
        <button
          type="button"
          style={btnSecondary}
          disabled={busy || bulkEnemyBusy || selectedInFamily === 0}
          data-testid={`registry-enemy-bulk-pool-${family}`}
          onClick={() => onBulkEnemySetInPool(family)}
        >
          Set selected → In pool
        </button>
        <button
          type="button"
          style={btnSecondary}
          disabled={busy || bulkEnemyBusy || selectedInFamily === 0}
          data-testid={`registry-enemy-bulk-delete-${family}`}
          onClick={() => onBulkEnemyDeleteSelected(family)}
        >
          Delete selected
        </button>
      </div>
      <div style={{ overflowX: "auto", width: "100%" }}>
        <table style={{ width: "100%", minWidth: 480, borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #3c3c3c" }}>
              <th style={{ ...th, width: 36 }}>
                <FamilyVersionSelectAllCheckbox
                  family={family}
                  allSelected={allSelected}
                  someSelected={someSelected}
                  disabled={busy || bulkEnemyBusy}
                  onChange={(checked) => onEnemyFamilySelectAllVersions(family, checked)}
                />
              </th>
              <th style={th}>Version id</th>
              <th style={th}>Tags</th>
              <th style={th}>Name</th>
              <th style={{ ...th, maxWidth: 140 }}>Path</th>
              <th style={th}>Spawn state</th>
              <th style={th}>Preview</th>
              <th style={th}>Delete</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((row) => {
              const key = `${family}:${row.id}`;
              const pending = busyKey === key || deleteBusyKey === key || bulkEnemyBusy;
              const deletePlan = getEnemyDeletePlan(family, row);
              const rowSelectKey = enemyRegistryRowKey(family, row.id);
              return (
                <tr key={key} style={{ borderBottom: "1px solid #2d2d2d" }}>
                  <td style={td}>
                    <input
                      type="checkbox"
                      checked={selectedEnemyVersionKeys.has(rowSelectKey)}
                      disabled={pending}
                      aria-label={`Select ${row.id}`}
                      data-testid={`registry-enemy-select-${family}-${row.id}`}
                      onChange={() => onToggleEnemyVersionSelect(family, row.id)}
                    />
                  </td>
                  <td style={td}>{row.id}</td>
                  <td style={{ ...td, minWidth: 120, maxWidth: 220 }}>
                    <RegistryTagEditor
                      family={family}
                      version={row}
                      knownTags={knownTags}
                      hideDisplayTags={hideDisplayTags}
                      disabled={pending}
                      onCommit={(tags) => onPatchTags(family, row, tags)}
                    />
                  </td>
                  <td style={td}>
                    <RegistryVersionNameInput
                      versionId={row.id}
                      storedName={row.name}
                      disabled={pending}
                      onCommit={(trimmed) => void onRenameVersion(family, row, trimmed)}
                    />
                  </td>
                  <td style={{ ...td, maxWidth: 180, wordBreak: "break-all", fontSize: 10, color: "#9d9d9d" }}>
                    {row.path}
                  </td>
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
                      disabled={pending}
                      title={`Load ${row.id} into the 3D preview`}
                      onClick={() => onPreviewVersion(family, row)}
                    >
                      Preview
                    </button>
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
    </div>
  );
}
