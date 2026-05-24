import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS } from "../../constants/elements";
import { useAppStore } from "../../store/useAppStore";
import { useStudioRunActions } from "../../hooks/useStudioRunActions";
import {
  formatCommandPreview,
  parseCommandPreview,
} from "../CommandPanel/commandLogic";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import {
  resolveStudioCodeSourcePath,
  STUDIO_CODE_SOURCE_TABS,
  type StudioCodeSourceId,
} from "../../utils/studioCodeSources";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_PANEL,
} from "../../styles/studioTokens";
import { StudioEditorSurface } from "./StudioEditorSurface";
import { StudioPanelHead } from "./StudioPanelHead";

function logLineColor(text: string): string {
  if (text.includes("Error") || (text.includes("exit ") && text.includes("):"))) return "#f48771";
  if (text.startsWith("✓") || text.includes("complete")) return "#94e3b6";
  if (text.startsWith("---")) return STUDIO_INK_MUTED;
  return STUDIO_INK_SECONDARY;
}

function sourceTabStyle(active: boolean, accentHue: string, accentSoft: string): CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 5,
    background: active ? accentSoft : STUDIO_SURFACE_PANEL,
    border: active ? `1px solid ${accentHue}40` : "1px solid rgba(255,255,255,0.04)",
    color: active ? accentHue : STUDIO_INK_SECONDARY,
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  };
}

const actionBtn: CSSProperties = {
  padding: "5px 12px",
  borderRadius: 6,
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "inherit",
  border: "1px solid rgba(255,255,255,0.06)",
};

export function StudioCodePanel() {
  const commandContext = useAppStore((s) => s.commandContext);
  const animatedEnemyMeta = useAppStore((s) => s.animatedEnemyMeta);
  const commandExportFinish = useAppStore((s) => s.commandExportFinish);
  const commandExportHexColor = useAppStore((s) => s.commandExportHexColor);
  const setCommandExport = useAppStore((s) => s.setCommandExport);
  const terminalLines = useAppStore((s) => s.terminalLines);
  const clearTerminal = useAppStore((s) => s.clearTerminal);
  const selectFile = useAppStore((s) => s.selectFile);

  const [sourceId, setSourceId] = useState<StudioCodeSourceId>("cli");
  const [commandPreview, setCommandPreview] = useState("");
  const [commandPreviewDirty, setCommandPreviewDirty] = useState(false);
  const [commandPreviewError, setCommandPreviewError] = useState<string | null>(null);

  const cmd = commandContext.cmd;
  const enemy = commandContext.enemy;
  const finish = commandExportFinish;
  const hexColor = commandExportHexColor;

  const elementId = useMemo(() => {
    if (cmd === "animated" && enemy.trim()) return inferFamilyElementId(enemy.trim(), []);
    return "physical" as const;
  }, [cmd, enemy]);

  const accentHue = ELEMENTS[elementId].hue;
  const accentSoft = ELEMENTS[elementId].soft;

  const runFields = useMemo(
    () => ({
      cmd,
      enemy,
      description: "",
      difficulty: "normal",
      finish,
      hexColor,
      commandPreviewDirty,
    }),
    [cmd, enemy, finish, hexColor, commandPreviewDirty],
  );

  const { isRunning, runValidationError, canRegenerate, canRun, regenerateTitle, handleRun } =
    useStudioRunActions(runFields);

  useEffect(() => {
    if (commandPreviewDirty) return;
    setCommandPreview(
      formatCommandPreview({ cmd, enemy, description: "", difficulty: "normal", finish, hexColor }),
    );
  }, [cmd, enemy, finish, hexColor, commandPreviewDirty]);

  const openSource = useCallback(
    async (next: StudioCodeSourceId) => {
      setSourceId(next);
      if (next === "cli") return;
      const path = resolveStudioCodeSourcePath(next, cmd, enemy, animatedEnemyMeta);
      if (!path) return;
      await selectFile(path);
    },
    [cmd, enemy, animatedEnemyMeta, selectFile],
  );

  function applyParsedPreview() {
    const parsed = parseCommandPreview(commandPreview);
    if (!parsed.next || parsed.error) {
      setCommandPreviewError(parsed.error ?? "Unable to parse command preview.");
      return;
    }
    const next = parsed.next;
    useAppStore.setState((s) => {
      s.commandContext = {
        cmd: next.cmd,
        enemy: next.enemy ?? "",
      };
    });
    if (next.cmd === "animated" || next.cmd === "player") {
      setCommandExport({
        finish: next.finish ?? finish,
        hexColor: next.hexColor ?? "",
      });
    }
    setCommandPreviewDirty(false);
    setCommandPreviewError(null);
  }

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(commandPreview);
    } catch {
      /* ignore */
    }
  }

  const logTail = terminalLines.slice(-40);

  return (
    <div
      data-testid="studio-code-panel"
      style={{ display: "flex", flexDirection: "column", gap: 14, minHeight: 0, flex: 1 }}
    >
      <StudioPanelHead
        title="Generation command"
        subtitle="Edit, run, and view output"
        right={
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              style={{
                ...actionBtn,
                background: STUDIO_SURFACE_PANEL,
                color: STUDIO_INK_SECONDARY,
                opacity: isRunning || !canRun ? 0.45 : 1,
              }}
              disabled={isRunning || !canRun}
              onClick={() => void handleRun(false)}
            >
              Run
            </button>
            <button
              type="button"
              data-testid="studio-code-regenerate"
              style={{
                ...actionBtn,
                background: canRegenerate ? accentHue : STUDIO_SURFACE_PANEL,
                color: canRegenerate ? "#0c0c10" : STUDIO_INK_MUTED,
                opacity: isRunning || !canRegenerate ? 0.45 : 1,
              }}
              disabled={isRunning || !canRegenerate}
              title={regenerateTitle}
              onClick={() => void handleRun(true)}
            >
              Regenerate
            </button>
          </div>
        }
      />

      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }} role="tablist" aria-label="Code sources">
        {STUDIO_CODE_SOURCE_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={sourceId === tab.id}
            data-testid={`studio-code-source-${tab.id}`}
            style={sourceTabStyle(sourceId === tab.id, accentHue, accentSoft)}
            onClick={() => void openSource(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {sourceId === "cli" ? (
        <>
          <div
            style={{
              fontSize: 10,
              color: STUDIO_INK_MUTED,
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              lineHeight: 1.6,
            }}
          >
            Format: <span style={{ color: STUDIO_INK_SECONDARY }}>&lt;cmd&gt;</span>{" "}
            <span style={{ color: STUDIO_INK_MUTED }}>[enemy|color]</span>{" "}
            <span style={{ color: STUDIO_INK_MUTED }}>[--finish …] [--hex-color #RRGGBB]</span>
          </div>

          <div
            style={{
              background: "#08080c",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 9,
              overflow: "hidden",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            }}
          >
            <div
              style={{
                padding: "7px 10px",
                background: "rgba(255,255,255,0.02)",
                borderBottom: "1px solid rgba(255,255,255,0.05)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ff5468" }} aria-hidden />
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ffd23d" }} aria-hidden />
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#4cb87d" }} aria-hidden />
              <span style={{ fontSize: 10, color: STUDIO_INK_MUTED, marginLeft: 6 }}>preview · {cmd}</span>
              <div style={{ flex: 1 }} />
              <button
                type="button"
                title="Copy command"
                style={{
                  background: "transparent",
                  border: 0,
                  color: STUDIO_INK_MUTED,
                  fontSize: 11,
                  cursor: "pointer",
                }}
                onClick={() => void copyCommand()}
              >
                ⧉
              </button>
            </div>
            <div style={{ padding: "8px 10px", display: "flex", gap: 8, alignItems: "flex-start" }}>
              <span style={{ color: accentHue, fontWeight: 700, userSelect: "none" }}>$</span>
              <textarea
                data-testid="studio-code-command-input"
                value={commandPreview}
                spellCheck={false}
                aria-label="Generation command"
                style={{
                  flex: 1,
                  minHeight: 52,
                  resize: "vertical",
                  border: 0,
                  background: "transparent",
                  color: STUDIO_INK_PRIMARY,
                  fontSize: 12,
                  lineHeight: 1.65,
                  fontFamily: "inherit",
                  outline: "none",
                }}
                onChange={(e) => {
                  setCommandPreview(e.target.value);
                  setCommandPreviewDirty(true);
                  setCommandPreviewError(null);
                }}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button
              type="button"
              style={{
                ...actionBtn,
                background: commandPreviewDirty ? accentHue : STUDIO_SURFACE_PANEL,
                color: commandPreviewDirty ? "#0c0c10" : STUDIO_INK_MUTED,
              }}
              disabled={!commandPreviewDirty}
              onClick={applyParsedPreview}
            >
              Apply
            </button>
            {commandPreviewError ? (
              <span style={{ color: "#f48771", fontSize: 11 }}>{commandPreviewError}</span>
            ) : null}
            {runValidationError ? (
              <span style={{ color: "#f48771", fontSize: 11 }}>{runValidationError}</span>
            ) : null}
          </div>
        </>
      ) : (
        <StudioEditorSurface accentHue={accentHue} />
      )}

      <div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 8,
          }}
        >
          <span
            style={{
              fontSize: 10,
              color: STUDIO_INK_MUTED,
              fontWeight: 600,
              letterSpacing: 0.6,
              textTransform: "uppercase",
            }}
          >
            Log output
          </span>
          <button
            type="button"
            style={{
              background: "transparent",
              border: 0,
              color: STUDIO_INK_MUTED,
              fontSize: 10,
              cursor: "pointer",
            }}
            onClick={clearTerminal}
          >
            Clear
          </button>
        </div>
        <div
          data-testid="studio-code-log"
          style={{
            background: "#08080c",
            border: "1px solid rgba(255,255,255,0.04)",
            borderRadius: 8,
            padding: "10px 12px",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: 11,
            lineHeight: 1.7,
            maxHeight: 200,
            overflowY: "auto",
          }}
        >
          {logTail.length === 0 ? (
            <div style={{ color: STUDIO_INK_MUTED }}>Run or Regenerate to see output here.</div>
          ) : (
            logTail.map((line) => (
              <div key={line.id} style={{ color: logLineColor(line.text) }}>
                {line.text}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
