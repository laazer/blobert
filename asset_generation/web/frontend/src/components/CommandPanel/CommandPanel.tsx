import { useEffect, useState } from "react";
import { fetchEnemies, killProcess } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { useStreamingOutput } from "../Terminal/useStreamingOutput";
import { RunCmd } from "../../types";

const ALL_CMDS: RunCmd[] = ["animated", "player", "level", "smart", "stats", "test"];

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
};

export function CommandPanel() {
  const isRunning = useAppStore((state) => state.isRunning);
  const clearTerminal = useAppStore((state) => state.clearTerminal);
  const saveFile = useAppStore((state) => state.saveFile);
  const isDirty = useAppStore((state) => state.isDirty);

  const [cmd, setCmd] = useState<RunCmd>("animated");
  const [enemy, setEnemy] = useState("adhesion_bug");
  const [count, setCount] = useState(1);
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState("normal");
  const [enemies, setEnemies] = useState<string[]>([]);

  const { start, startTests } = useStreamingOutput();

  useEffect(() => {
    fetchEnemies().then(setEnemies).catch(() => {});
  }, []);

  const showEnemy = ["animated", "player", "level", "stats"].includes(cmd);
  const showCount = ["animated", "player", "level"].includes(cmd);
  const showDescription = cmd === "smart";
  const showDifficulty = ["smart", "stats"].includes(cmd);

  async function handleRun() {
    clearTerminal();
    if (isDirty) await saveFile();
    start({ cmd, enemy: showEnemy ? enemy : undefined, count: showCount ? count : undefined,
            description: showDescription ? description : undefined,
            difficulty: showDifficulty ? difficulty : undefined });
  }

  async function handleKill() {
    await killProcess();
  }

  return (
    <div style={s.panel}>
      <div style={s.row}>
        <span style={s.label}>cmd</span>
        <select style={s.select} value={cmd} onChange={(e) => setCmd(e.target.value as RunCmd)}>
          {ALL_CMDS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        {showEnemy && (
          <>
            <span style={s.label}>enemy</span>
            {enemies.length > 0 ? (
              <select style={s.select} value={enemy} onChange={(e) => setEnemy(e.target.value)}>
                {enemies.map((en) => <option key={en} value={en}>{en}</option>)}
              </select>
            ) : (
              <input style={s.textInput} value={enemy} onChange={(e) => setEnemy(e.target.value)} placeholder="enemy_name" />
            )}
          </>
        )}

        {showCount && (
          <>
            <span style={s.label}>count</span>
            <input style={s.input} type="number" min={1} max={10} value={count}
              onChange={(e) => setCount(parseInt(e.target.value, 10) || 1)} />
          </>
        )}
      </div>

      {showDescription && (
        <div style={s.row}>
          <span style={s.label}>desc</span>
          <input style={s.textInput} value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="a large fire spider with powerful attacks" />
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
        <button style={s.btn} onClick={saveFile} disabled={!isDirty}>Save</button>
        <button style={{ ...s.btn, opacity: isRunning ? 0.5 : 1 }} onClick={handleRun} disabled={isRunning}>
          Run
        </button>
        {isRunning && (
          <button style={s.killBtn} onClick={handleKill}>Kill</button>
        )}
        <button style={{ ...s.btn, background: "#555" }} onClick={startTests} disabled={isRunning}>
          Run pytest
        </button>
      </div>
    </div>
  );
}
