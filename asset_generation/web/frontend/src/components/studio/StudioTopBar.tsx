import { useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS } from "../../constants/elements";
import { useStudioRunActions } from "../../hooks/useStudioRunActions";
import { useAppStore } from "../../store/useAppStore";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import { registryFamilyTabLabel } from "../../utils/registryFamilyNav";
import { SaveScriptModal } from "../CommandPanel/SaveScriptModal";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_BAR,
  STUDIO_SURFACE_PANEL,
  STUDIO_TOP_BAR_HEIGHT_PX,
} from "../../styles/studioTokens";

const topBarRoot: CSSProperties = {
  gridColumn: "1 / 4",
  gridRow: 1,
  display: "flex",
  alignItems: "center",
  padding: "0 16px",
  gap: 14,
  height: STUDIO_TOP_BAR_HEIGHT_PX,
  background: STUDIO_SURFACE_BAR,
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  flexShrink: 0,
};

const logoMark: CSSProperties = {
  width: 26,
  height: 26,
  borderRadius: 7,
  background: "conic-gradient(from 180deg, #ff6b3d, #b87dff, #5dc1ff, #9fe830, #ff6b3d)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 800,
  color: "#0c0c10",
  fontSize: 13,
};

const breadcrumbMuted: CSSProperties = {
  fontSize: 13,
  color: STUDIO_INK_SECONDARY,
  fontWeight: 600,
};

const breadcrumbActive: CSSProperties = {
  fontSize: 13,
  color: STUDIO_INK_PRIMARY,
  fontWeight: 600,
};

const searchBtn: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  background: STUDIO_SURFACE_PANEL,
  border: "1px solid rgba(255,255,255,0.08)",
  color: "#9a9aa6",
  padding: "6px 12px",
  borderRadius: 8,
  fontSize: 12,
  cursor: "default",
  fontFamily: "inherit",
};

const solidBtn: CSSProperties = {
  padding: "6px 14px",
  borderRadius: 8,
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "inherit",
  background: STUDIO_SURFACE_PANEL,
  border: "1px solid rgba(255,255,255,0.08)",
  color: STUDIO_INK_SECONDARY,
};

export function StudioTopBar() {
  const commandContext = useAppStore((s) => s.commandContext);
  const commandExportFinish = useAppStore((s) => s.commandExportFinish);
  const commandExportHexColor = useAppStore((s) => s.commandExportHexColor);
  const selectedFile = useAppStore((s) => s.selectedFile);
  const fileTree = useAppStore((s) => s.fileTree);
  const isSaving = useAppStore((s) => s.isSaving);
  const saveEditorToPath = useAppStore((s) => s.saveEditorToPath);
  const loadFileTree = useAppStore((s) => s.loadFileTree);

  const [saveScriptModalOpen, setSaveScriptModalOpen] = useState(false);

  const familyLabel =
    commandContext.cmd === "animated" && commandContext.enemy
      ? registryFamilyTabLabel(commandContext.enemy)
      : commandContext.cmd;

  const elementId = useMemo(() => {
    if (commandContext.cmd === "animated" && commandContext.enemy.trim()) {
      return inferFamilyElementId(commandContext.enemy.trim(), []);
    }
    return "physical" as const;
  }, [commandContext.cmd, commandContext.enemy]);

  const accentHue = ELEMENTS[elementId].hue;

  const runFields = useMemo(
    () => ({
      cmd: commandContext.cmd,
      enemy: commandContext.enemy,
      description: "",
      difficulty: "normal",
      finish: commandExportFinish,
      hexColor: commandExportHexColor,
      commandPreviewDirty: false,
    }),
    [commandContext.cmd, commandContext.enemy, commandExportFinish, commandExportHexColor],
  );

  const { isRunning, canRegenerate, regenerateTitle, handleRun } = useStudioRunActions(runFields);

  return (
    <header style={topBarRoot} data-testid="studio-top-bar">
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={logoMark} aria-hidden>
          B
        </div>
        <span style={{ fontWeight: 700, fontSize: 13 }}>Blobert</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbMuted}>{familyLabel}</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbActive}>
          {commandContext.cmd === "animated" && commandContext.enemy ? "Look" : "Studio"}
        </span>
      </div>
      <div style={{ flex: 1 }} />
      <button type="button" style={searchBtn} disabled title="Search (Phase 2)">
        Search…
        <span
          style={{
            background: "#23232e",
            padding: "2px 6px",
            borderRadius: 4,
            fontSize: 10,
            color: STUDIO_INK_MUTED,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          }}
        >
          ⌘K
        </span>
      </button>
      <button
        type="button"
        style={solidBtn}
        disabled={isSaving}
        onClick={() => setSaveScriptModalOpen(true)}
        title="Save the current editor buffer to a project path"
      >
        Save
      </button>
      <button
        type="button"
        data-testid="studio-top-regenerate"
        style={{
          ...solidBtn,
          background: canRegenerate ? accentHue : STUDIO_SURFACE_PANEL,
          color: canRegenerate ? "#0c0c10" : STUDIO_INK_MUTED,
          border: canRegenerate ? `1px solid ${accentHue}80` : "1px solid rgba(255,255,255,0.08)",
          opacity: isRunning || !canRegenerate ? 0.5 : 1,
        }}
        disabled={isRunning || !canRegenerate}
        title={regenerateTitle}
        onClick={() => void handleRun(true)}
      >
        Regenerate
      </button>
      <SaveScriptModal
        open={saveScriptModalOpen}
        onClose={() => setSaveScriptModalOpen(false)}
        initialPath={selectedFile}
        fileTree={fileTree}
        onLoadFileTree={loadFileTree}
        isSaving={isSaving}
        onSave={saveEditorToPath}
      />
    </header>
  );
}
