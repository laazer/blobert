import type { CSSProperties } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { LoadExistingCandidate } from "../../api/client";
import { previewPathFromAssetsUrl } from "../../utils/previewPathFromAssetsUrl";
import { loadExistingCandidateKey, loadExistingCandidateLabel } from "./registryLoadExisting";
import { LOAD_EXISTING_EMPTY_COPY, PLAYER_RESTART_REQUIREMENT_COPY } from "./registryPaneStrings";

export const PLAYER_MODEL_SECTION_HEADING = "Player model";

const noteStyle: CSSProperties = { fontSize: 11, color: "#9d9d9d", marginBottom: 10, lineHeight: 1.45 };
const labelStyle: CSSProperties = { display: "block", marginBottom: 6, color: "#9d9d9d" };
const statusLabel: CSSProperties = { fontSize: 10, textTransform: "uppercase", letterSpacing: "0.04em", color: "#858585", marginBottom: 4 };
const statusValue: CSSProperties = { fontSize: 12, color: "#d4d4d4", wordBreak: "break-all", fontFamily: "ui-monospace, monospace" };
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
const divider: CSSProperties = { borderTop: "1px solid #2d2d2d", margin: "12px 0", paddingTop: 10 };

export type RegistryPlayerSectionProps = {
  activeGamePath: string | null;
  playerBusy: boolean;
  onOpenPickGameActive: () => void;
  loadExistingCandidates: LoadExistingCandidate[];
  loadExistingSelection: string;
  onLoadExistingSelectionChange: (key: string) => void;
  loadExistingBusy: boolean;
  onLoadExistingInPreview: () => void;
  onPreviewGameActive: () => void;
};

export function RegistryPlayerSection({
  activeGamePath,
  playerBusy,
  onOpenPickGameActive,
  loadExistingCandidates,
  loadExistingSelection,
  onLoadExistingSelectionChange,
  loadExistingBusy,
  onLoadExistingInPreview,
  onPreviewGameActive,
}: RegistryPlayerSectionProps) {
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const previewPath = previewPathFromAssetsUrl(activeGlbUrl);
  const previewMatchesGame = Boolean(previewPath && activeGamePath && previewPath === activeGamePath);

  return (
    <div style={{ ...sectionStyle, marginBottom: 16 }}>
      <h3 style={h3Style}>{PLAYER_MODEL_SECTION_HEADING}</h3>
      <div style={noteStyle}>
        The <strong>3D preview</strong> (right panel) and the <strong>game&apos;s active model</strong> (registry) are
        independent. Use the controls below to align them when you want.
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 8 }}>
        <div>
          <div style={statusLabel}>Editor preview</div>
          <div style={statusValue}>{previewPath ?? "— none —"}</div>
        </div>
        <div>
          <div style={statusLabel}>Game active (registry)</div>
          <div style={statusValue}>{activeGamePath ?? "— none —"}</div>
        </div>
      </div>
      {previewMatchesGame ? (
        <div style={{ fontSize: 10, color: "#6a9955", marginBottom: 8 }}>Preview matches game active path.</div>
      ) : (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: 8 }}>
          <button
            type="button"
            style={{ ...btnSecondary, opacity: activeGamePath ? 1 : 0.45 }}
            disabled={!activeGamePath || playerBusy}
            title="Load the registry’s active player .glb into the 3D preview"
            onClick={onPreviewGameActive}
          >
            Preview game active
          </button>
        </div>
      )}

      <div style={noteStyle}>{PLAYER_RESTART_REQUIREMENT_COPY}</div>

      <div style={{ marginBottom: 8 }}>
        <button
          type="button"
          style={btnPrimary}
          disabled={playerBusy}
          data-testid="player-active-model-open"
          title="Searchable list of allowlisted player .glb paths"
          onClick={onOpenPickGameActive}
        >
          Choose game active model…
        </button>
      </div>

      <div style={divider}>
        <div style={noteStyle}>
          Pick a draft or in-use registry entry, then load it into the <strong>3D preview</strong> (same path the server
          resolves for Blender workflows). Paths are allow-listed from the registry only.
        </div>
        {loadExistingCandidates.length === 0 ? (
          <div style={{ color: "#d7ba7d", fontSize: 11 }}>{LOAD_EXISTING_EMPTY_COPY}</div>
        ) : (
          <>
            <label style={labelStyle} htmlFor="load-existing-select">
              Registry model → preview
            </label>
            <select
              id="load-existing-select"
              style={selectStyle}
              disabled={loadExistingBusy}
              value={loadExistingSelection}
              onChange={(e) => onLoadExistingSelectionChange(e.target.value)}
            >
              {loadExistingCandidates.map((row) => (
                <option key={loadExistingCandidateKey(row)} value={loadExistingCandidateKey(row)}>
                  {loadExistingCandidateLabel(row)}
                </option>
              ))}
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
    </div>
  );
}
