import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import type { LoadExistingCandidate } from "../../api/client";
import {
  filterLoadExistingCandidates,
  loadExistingCandidateKey,
  loadExistingCandidateLabel,
} from "./registryLoadExisting";
import { LOAD_EXISTING_EMPTY_COPY } from "./registryPaneStrings";

const noteStyle: CSSProperties = { fontSize: 11, color: "#9d9d9d", marginBottom: 10, lineHeight: 1.45 };
const labelStyle: CSSProperties = { display: "block", marginBottom: 6, color: "#9d9d9d" };
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
const btnPrimary: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  border: "1px solid #0e639c",
  borderRadius: 3,
  cursor: "pointer",
  background: "#0e639c",
  color: "#d4d4d4",
};

export const REGISTRY_ENEMY_LOAD_EXISTING_HEADING = "Load existing (enemy / animated)";

export type RegistryEnemyLoadExistingSectionProps = {
  loadExistingCandidates: LoadExistingCandidate[];
  loadExistingSelection: string;
  onLoadExistingSelectionChange: (key: string) => void;
  loadExistingBusy: boolean;
  onLoadExistingInPreview: () => void;
};

export function RegistryEnemyLoadExistingSection({
  loadExistingCandidates,
  loadExistingSelection,
  onLoadExistingSelectionChange,
  loadExistingBusy,
  onLoadExistingInPreview,
}: RegistryEnemyLoadExistingSectionProps) {
  const [enemyFamilyFilter, setEnemyFamilyFilter] = useState<string | null>(null);

  const enemyFamiliesInCandidates = useMemo(() => {
    const s = new Set<string>();
    for (const r of loadExistingCandidates) {
      if (r.kind === "enemy") s.add(r.family);
    }
    return [...s].sort();
  }, [loadExistingCandidates]);

  const visibleLoadExistingCandidates = useMemo(
    () => filterLoadExistingCandidates(loadExistingCandidates, "enemy", enemyFamilyFilter),
    [loadExistingCandidates, enemyFamilyFilter],
  );

  useEffect(() => {
    const ok = visibleLoadExistingCandidates.some((r) => loadExistingCandidateKey(r) === loadExistingSelection);
    if (ok) return;
    if (visibleLoadExistingCandidates.length > 0) {
      onLoadExistingSelectionChange(loadExistingCandidateKey(visibleLoadExistingCandidates[0]));
    } else {
      onLoadExistingSelectionChange("");
    }
  }, [visibleLoadExistingCandidates, loadExistingSelection, onLoadExistingSelectionChange]);

  return (
    <div style={{ ...sectionStyle, marginBottom: 16 }}>
      <h3 style={h3Style}>{REGISTRY_ENEMY_LOAD_EXISTING_HEADING}</h3>
      <div style={noteStyle}>
        Pick a draft or in-use <strong>enemy</strong> registry entry, then load it into the <strong>3D preview</strong>.
        Paths are allow-listed from the registry only.
      </div>
      {loadExistingCandidates.length === 0 ? (
        <div style={{ color: "#d7ba7d", fontSize: 11 }}>{LOAD_EXISTING_EMPTY_COPY}</div>
      ) : (
        <>
          {enemyFamiliesInCandidates.length > 0 ? (
            <div style={{ marginBottom: 8 }}>
              <label style={labelStyle} htmlFor="load-existing-enemy-family-animated-tab">
                Enemy family
              </label>
              <select
                id="load-existing-enemy-family-animated-tab"
                style={selectStyle}
                disabled={loadExistingBusy}
                value={enemyFamilyFilter ?? ""}
                onChange={(e) => setEnemyFamilyFilter(e.target.value === "" ? null : e.target.value)}
              >
                <option value="">All families</option>
                {enemyFamiliesInCandidates.map((fam) => (
                  <option key={fam} value={fam}>
                    {fam}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          <label style={labelStyle} htmlFor="load-existing-select-enemy-tab">
            Registry model → preview
          </label>
          <select
            id="load-existing-select-enemy-tab"
            style={selectStyle}
            disabled={loadExistingBusy}
            value={loadExistingSelection}
            onChange={(e) => onLoadExistingSelectionChange(e.target.value)}
          >
            {visibleLoadExistingCandidates.length === 0 ? (
              <option value="">No enemy matches for current filters</option>
            ) : (
              visibleLoadExistingCandidates.map((row) => (
                <option key={loadExistingCandidateKey(row)} value={loadExistingCandidateKey(row)}>
                  {loadExistingCandidateLabel(row)}
                </option>
              ))
            )}
          </select>
          <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button
              type="button"
              style={btnPrimary}
              disabled={loadExistingBusy || !loadExistingSelection}
              title="Resolve path on the server and load that .glb in the 3D viewer"
              onClick={onLoadExistingInPreview}
            >
              Load in preview
            </button>
          </div>
        </>
      )}
    </div>
  );
}
