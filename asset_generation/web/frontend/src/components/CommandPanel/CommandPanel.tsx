import { useEffect, useState } from "react";
import { killProcess } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { useStreamingOutput } from "../Terminal/useStreamingOutput";
import { RunCmd } from "../../types";
import { enemySelectOptionLabel, normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import {
  ALL_CMDS,
  CMD_CONFIG,
  formatCommandPreview,
  ENEMY_FINISHES,
  getEnemyOptions,
  normalizeEnemyForCmd,
  parseCommandPreview,
  PLAYER_COLORS,
  PLAYER_FINISHES,
} from "./commandLogic";

const s: Record<string, React.CSSProperties> = {
  panel: {
    padding: "8px",
    background: "#252526",
    borderTop: "1px solid #3c3c3c",
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  row: { display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" },
  select: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 12,
  },
  input: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 12,
    width: 60,
  },
  textInput: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 12,
    flex: 1,
  },
  btn: {
    background: "#0e639c",
    color: "#fff",
    border: "none",
    borderRadius: 3,
    padding: "3px 10px",
    cursor: "pointer",
    fontSize: 12,
  },
  killBtn: {
    background: "#a12",
    color: "#fff",
    border: "none",
    borderRadius: 3,
    padding: "3px 10px",
    cursor: "pointer",
    fontSize: 12,
  },
  label: { color: "#9d9d9d", fontSize: 11 },
  helperText: { color: "#8f8f8f", fontSize: 11 },
  warningText: { color: "#e2b714", fontSize: 11 },
  errorText: { color: "#f48771", fontSize: 11 },
};

export function CommandPanel() {
  const isRunning = useAppStore((state) => state.isRunning);
  const clearTerminal = useAppStore((state) => state.clearTerminal);
  const saveFile = useAppStore((state) => state.saveFile);
  const isDirty = useAppStore((state) => state.isDirty);
  const setCommandContext = useAppStore((state) => state.setCommandContext);
  const animatedEnemyMeta = useAppStore((state) => state.animatedEnemyMeta);
  const animatedBuildOptionValues = useAppStore((state) => state.animatedBuildOptionValues);
  const animatedBuildControls = useAppStore((state) => state.animatedBuildControls);
  const enemyMetaError = useAppStore((state) => state.enemyMetaError);
  const metaBackend = useAppStore((state) => state.metaBackend);
  const metaBackendDetail = useAppStore((state) => state.metaBackendDetail);

  const [cmd, setCmd] = useState<RunCmd>("animated");
  const [enemy, setEnemy] = useState("spider");
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState("normal");
  const [finish, setFinish] = useState("glossy");
  const [hexColor, setHexColor] = useState("");
  const [commandPreview, setCommandPreview] = useState("");
  const [commandPreviewDirty, setCommandPreviewDirty] = useState(false);
  const [commandPreviewError, setCommandPreviewError] = useState<string | null>(null);
  const [cmdTransitionHint, setCmdTransitionHint] = useState<string | null>(null);

  const { start } = useStreamingOutput();

  const cfg = CMD_CONFIG[cmd];
  const showEnemy = cfg.showEnemy;
  const showDescription = cfg.showDescription;
  const showDifficulty = cfg.showDifficulty;
  const enemySlugsForCmd =
    cmd === "player" ? [] : animatedEnemyMeta.map((m) => m.slug);
  const enemyOptions = getEnemyOptions(cmd, enemySlugsForCmd);

  useEffect(() => {
    setCommandContext({ cmd, enemy: showEnemy ? enemy : "" });
  }, [cmd, enemy, showEnemy, setCommandContext]);

  useEffect(() => {
    const nextEnemy = normalizeEnemyForCmd(cmd, enemy, enemySlugsForCmd);
    if (nextEnemy !== enemy) setEnemy(nextEnemy);
  }, [cmd, enemy, enemySlugsForCmd]);

  useEffect(() => {
    if (commandPreviewDirty) return;
    setCommandPreview(formatCommandPreview({ cmd, enemy, description, difficulty, finish, hexColor }));
  }, [cmd, enemy, description, difficulty, finish, hexColor, commandPreviewDirty]);

  function handleCmdChange(nextCmd: RunCmd) {
    const nextCfg = CMD_CONFIG[nextCmd];
    const prevCfg = CMD_CONFIG[cmd];
    setCmd(nextCmd);
    setCommandPreviewDirty(false);
    setCommandPreviewError(null);
    const dropped: string[] = [];
    if (prevCfg.showEnemy && !nextCfg.showEnemy && enemy.trim()) dropped.push("enemy");
    if (prevCfg.showDescription && !nextCfg.showDescription && description.trim()) dropped.push("description");
    if (prevCfg.showDifficulty && !nextCfg.showDifficulty) dropped.push("difficulty");
    if (!nextCfg.showEnemy) setEnemy("");
    if (!nextCfg.showDescription) setDescription("");
    if (!nextCfg.showDifficulty) setDifficulty("normal");
    setCmdTransitionHint(dropped.length > 0 ? `Switched to '${nextCmd}': ${dropped.join(", ")} hidden/reset.` : null);
  }

  function applyParsedPreview() {
    const parsed = parseCommandPreview(commandPreview);
    if (!parsed.next || parsed.error) {
      setCommandPreviewError(parsed.error ?? "Unable to parse command preview.");
      return;
    }
    const next = parsed.next;
    setCmd(next.cmd);
    setEnemy(next.enemy ?? "");
    setDescription(next.description ?? "");
    setDifficulty(next.difficulty ?? "normal");
    setFinish(next.finish ?? "glossy");
    setHexColor(next.hexColor ?? "");
    setCommandPreviewDirty(false);
    setCommandPreviewError(null);
    setCmdTransitionHint(null);
  }

  const runValidationError = (() => {
    if (commandPreviewDirty) return "Apply command preview changes before running.";
    if (showEnemy && cfg.requiresEnemy && !enemy.trim()) return "Enemy is required for this cmd.";
    if (cmd === "player" && !PLAYER_COLORS.includes(enemy)) {
      return `Player cmd requires a slime color (${PLAYER_COLORS.join(", ")}).`;
    }
    if (cmd === "player" && !PLAYER_FINISHES.includes(finish)) {
      return `Player finish must be one of: ${PLAYER_FINISHES.join(", ")}.`;
    }
    if (cmd === "animated" && !ENEMY_FINISHES.includes(finish)) {
      return `Enemy finish must be one of: ${ENEMY_FINISHES.join(", ")}.`;
    }
    if (cmd === "player" && hexColor && !/^#[0-9a-fA-F]{6}$/.test(hexColor)) {
      return "Custom color must be in #RRGGBB format.";
    }
    if (cmd === "animated" && hexColor && !/^#[0-9a-fA-F]{6}$/.test(hexColor)) {
      return "Custom color must be in #RRGGBB format.";
    }
    return null;
  })();

  async function handleRun() {
    if (isDirty) await saveFile();
    if (runValidationError) return;
    const singleOutputCmd = cmd === "animated" || cmd === "player" || cmd === "level";
    let buildOptionsJson: string | undefined;
    if (cmd === "animated" && enemy && enemy !== "all") {
      const slug = normalizeAnimatedSlug(enemy);
      const opts = animatedBuildOptionValues[slug];
      if (opts && Object.keys(opts).length > 0) {
        const defs = animatedBuildControls[slug] ?? [];
        const meshKeys = new Set(
          defs.filter((d) => d.type === "float").map((d) => d.key),
        );
        const top: Record<string, unknown> = {};
        const mesh: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(opts)) {
          if (meshKeys.has(k)) mesh[k] = v;
          else top[k] = v;
        }
        if (Object.keys(mesh).length > 0) top.mesh = mesh;
        buildOptionsJson = JSON.stringify({ [slug]: top });
      }
    }
    start({
      cmd,
      enemy: showEnemy ? enemy : undefined,
      count: singleOutputCmd ? 1 : undefined,
      description: showDescription ? description : undefined,
      difficulty: showDifficulty ? difficulty : undefined,
      finish: (cmd === "player" || cmd === "animated") ? finish : undefined,
      hexColor: (cmd === "player" || cmd === "animated") && hexColor ? hexColor : undefined,
      buildOptionsJson,
    });
  }

  async function handleKill() {
    await killProcess();
  }

  return (
    <div style={s.panel}>
      <div style={s.row}>
        <span style={s.label}>cmd</span>
        <select style={s.select} value={cmd} onChange={(e) => handleCmdChange(e.target.value as RunCmd)}>
          {ALL_CMDS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        {showEnemy && (
          <>
            <span style={s.label}>{cmd === "player" ? "color" : "enemy"}</span>
            {enemyOptions.length > 0 ? (
              <select style={s.select} value={enemy} onChange={(e) => setEnemy(e.target.value)}>
                {enemyOptions.map((en) => (
                  <option key={en} value={en}>
                    {enemySelectOptionLabel(cmd, en, animatedEnemyMeta)}
                  </option>
                ))}
              </select>
            ) : (
              <input
                style={s.textInput}
                value={enemy}
                onChange={(e) => setEnemy(e.target.value)}
                placeholder="slug (e.g. spider)"
              />
            )}
          </>
        )}

      </div>

      <div style={s.row}>
        <span style={s.label}>preview</span>
        <input
          style={s.textInput}
          value={commandPreview}
          onChange={(e) => {
            setCommandPreview(e.target.value);
            setCommandPreviewDirty(true);
            setCommandPreviewError(null);
          }}
          placeholder='animated spider --finish matte --hex-color #4b627c'
        />
        <button style={s.btn} onClick={applyParsedPreview} disabled={!commandPreviewDirty}>Apply</button>
      </div>
      <div style={s.row}>
        <span style={s.helperText}>Format: &lt;cmd&gt; [enemy|color] [--description \"...\"] [--difficulty ...] [--finish ...] [--hex-color #RRGGBB]</span>
      </div>
      {commandPreviewError && <div style={s.errorText}>{commandPreviewError}</div>}
      {cmdTransitionHint && <div style={s.warningText}>{cmdTransitionHint}</div>}
      {enemyMetaError && <div style={s.warningText}>Enemy list unavailable: {enemyMetaError}</div>}
      {metaBackend === "fallback" && (
        <div style={s.warningText}>
          Build controls unavailable (server import fallback).{" "}
          {metaBackendDetail ? `— ${metaBackendDetail}` : "Run task editor from the repo root (API on port 8000)."}
        </div>
      )}

      {showDescription && (
        <div style={s.row}>
          <span style={s.label}>desc</span>
          <input style={s.textInput} value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="a large fire spider with powerful attacks" />
        </div>
      )}

      {(cmd === "player" || cmd === "animated") && (
        <div style={s.row}>
          <span style={s.label}>finish</span>
          <select style={s.select} value={finish} onChange={(e) => setFinish(e.target.value)}>
            {(cmd === "player" ? PLAYER_FINISHES : ENEMY_FINISHES).map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
          <span style={s.label}>hex</span>
          <input
            style={{ ...s.select, width: 34, padding: 0, height: 24 }}
            type="color"
            value={/^#[0-9a-fA-F]{6}$/.test(hexColor) ? hexColor : "#7ab8ff"}
            onChange={(e) => setHexColor(e.target.value)}
          />
          <input
            style={{ ...s.textInput, maxWidth: 120 }}
            value={hexColor}
            onChange={(e) => setHexColor(e.target.value)}
            placeholder="#66ccff"
          />
          <button style={{ ...s.btn, background: "#555" }} type="button" onClick={() => setHexColor("")}>
            Use palette color
          </button>
        </div>
      )}

      {showDifficulty && (
        <div style={s.row}>
          <span style={s.label}>difficulty</span>
          <select style={s.select} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {["easy", "normal", "hard", "nightmare"].map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
      )}

      <div style={s.row}>
        {isDirty && <span style={{ color: "#e2b714", fontSize: 11 }}>unsaved changes</span>}
        {runValidationError && <span style={s.errorText}>{runValidationError}</span>}
        <button style={s.btn} onClick={saveFile} disabled={!isDirty}>Save</button>
        <button style={{ ...s.btn, opacity: isRunning ? 0.5 : 1 }} onClick={handleRun} disabled={isRunning}>
          Run
        </button>
        {isRunning && (
          <button style={s.killBtn} onClick={handleKill}>Kill</button>
        )}
        <button style={{ ...s.btn, background: "#444" }} onClick={clearTerminal} disabled={isRunning}>
          Clear
        </button>
      </div>
    </div>
  );
}
