import { useMemo, type CSSProperties } from "react";
import projectIconUrl from "@blobert/project-icon";
import { ELEMENTS } from "../../constants/elements";
import { useStudioPreviewVersion } from "../../hooks/useStudioPreviewVersion";
import { useStudioRunActions } from "../../hooks/useStudioRunActions";
import { useAppStore } from "../../store/useAppStore";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import { registryFamilyTabLabel } from "../../utils/registryFamilyNav";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_BAR,
  STUDIO_SURFACE_PANEL,
  STUDIO_TOP_BAR_HEIGHT_PX,
} from "../../styles/studioTokens";
import { StudioTopBarBreadcrumbTags } from "./StudioTopBarBreadcrumbTags";

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

const logoImg: CSSProperties = {
  width: 26,
  height: 26,
  borderRadius: 7,
  objectFit: "cover",
  flexShrink: 0,
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

const generateNewTitle =
  "Export a new GLB variant (next index). Does not overwrite the model currently in preview.";

export function StudioTopBar() {
  const commandContext = useAppStore((s) => s.commandContext);
  const commandExportFinish = useAppStore((s) => s.commandExportFinish);
  const commandExportHexColor = useAppStore((s) => s.commandExportHexColor);

  const { versionLabel, breadcrumbTags } = useStudioPreviewVersion();

  const familyLabel =
    commandContext.cmd === "animated" && commandContext.enemy
      ? registryFamilyTabLabel(commandContext.enemy)
      : commandContext.cmd === "player" && commandContext.enemy
        ? `Player · ${commandContext.enemy}`
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

  const { isRunning, canRegenerate, canRun, regenerateTitle, handleRun } = useStudioRunActions(runFields);

  const activeCrumb = versionLabel ?? (commandContext.cmd === "animated" && commandContext.enemy ? "Look" : "Studio");

  return (
    <header style={topBarRoot} data-testid="studio-top-bar">
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", minWidth: 0 }}>
        <img src={projectIconUrl} alt="" style={logoImg} width={26} height={26} aria-hidden />
        <span style={{ fontWeight: 700, fontSize: 13 }}>Blobert</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbMuted}>{familyLabel}</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbActive} data-testid="studio-top-bar-version-label">
          {activeCrumb}
        </span>
        <StudioTopBarBreadcrumbTags tags={breadcrumbTags} />
      </div>
      <div style={{ flex: 1 }} />
      <button
        type="button"
        data-testid="studio-top-generate-new"
        style={{
          ...solidBtn,
          opacity: isRunning || !canRun ? 0.5 : 1,
        }}
        disabled={isRunning || !canRun}
        title={generateNewTitle}
        onClick={() => void handleRun(false)}
      >
        Generate new
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
    </header>
  );
}
