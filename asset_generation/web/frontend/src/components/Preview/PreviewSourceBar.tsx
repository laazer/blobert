import { useCallback, useEffect, useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import { enemySelectOptionLabel } from "../../utils/enemyDisplay";
import {
  getAnimationCodeExtras,
  getAnimationCodeTarget,
  getMeshPartTree,
  getModelCodeTarget,
  PartTreeNode,
} from "./quickSourceNav";

const s: Record<string, React.CSSProperties> = {
  bar: {
    background: "#1e1e1e",
    borderBottom: "1px solid #3c3c3c",
    padding: "4px 8px",
    display: "flex",
    flexDirection: "column",
    gap: 4,
    flexShrink: 0,
  },
  row: { display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" },
  btn: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "3px 10px",
    cursor: "pointer",
    fontSize: 11,
  },
  btnPrimary: {
    background: "#0e639c",
    color: "#fff",
    border: "1px solid #0e639c",
    borderRadius: 3,
    padding: "3px 10px",
    cursor: "pointer",
    fontSize: 11,
  },
  btnDisabled: {
    opacity: 0.45,
    cursor: "not-allowed",
  },
  btnSmall: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 8px",
    cursor: "pointer",
    fontSize: 10,
  },
  hint: { color: "#8f8f8f", fontSize: 10 },
  err: { color: "#f48771", fontSize: 10 },
  tree: {
    background: "#252526",
    border: "1px solid #3c3c3c",
    borderRadius: 3,
    padding: "4px 6px",
    maxHeight: 280,
    overflowY: "auto",
    fontSize: 11,
    color: "#c8c8c8",
  },
  treeToggle: {
    background: "transparent",
    border: "none",
    color: "#9d9d9d",
    cursor: "pointer",
    fontSize: 11,
    padding: 0,
  },
};

function PartTreeRows({ nodes, depth }: { nodes: PartTreeNode[]; depth: number }) {
  return (
    <>
      {nodes.map((n) => (
        <div key={n.id}>
          <div style={{ paddingLeft: depth * 12, paddingTop: 2, paddingBottom: 2 }}>
            {n.children && n.children.length > 0 ? "▸ " : "• "}
            {n.label}
          </div>
          {n.children && n.children.length > 0 ? (
            <PartTreeRows nodes={n.children} depth={depth + 1} />
          ) : null}
        </div>
      ))}
    </>
  );
}

function shortLabelForAnimationExtra(path: string): string {
  if (path.includes("keyframe_system")) return "Keyframes";
  if (path.includes("body_types")) return "Body types";
  if (path.includes("animated_slug")) return "Example rig";
  if (path.includes("player_armature")) return "Armature";
  return path.replace(/^.*\//, "").replace(/\.py$/, "");
}

export function PreviewSourceBar() {
  const commandContext = useAppStore((st) => st.commandContext);
  const selectFile = useAppStore((st) => st.selectFile);
  const setEditorPaneVisible = useAppStore((st) => st.setEditorPaneVisible);
  const animatedEnemyMeta = useAppStore((st) => st.animatedEnemyMeta);
  const animatedBuildOptionValues = useAppStore((st) => st.animatedBuildOptionValues);
  const loadAnimatedEnemyMeta = useAppStore((st) => st.loadAnimatedEnemyMeta);
  const [navError, setNavError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [partsOpen, setPartsOpen] = useState(true);

  const { cmd, enemy } = commandContext;

  useEffect(() => {
    loadAnimatedEnemyMeta().catch(() => {});
  }, [loadAnimatedEnemyMeta]);

  const modelTarget = getModelCodeTarget(cmd, enemy, animatedEnemyMeta);
  const animTarget = getAnimationCodeTarget(cmd, enemy);
  const animExtras = getAnimationCodeExtras(cmd);
  const buildOpts = animatedBuildOptionValues[enemy] ?? {};
  const partTree = getMeshPartTree(cmd, enemy, animatedEnemyMeta, buildOpts);

  const openPath = useCallback(
    async (path: string | undefined) => {
      if (!path) return;
      setNavError(null);
      setBusy(true);
      try {
        setEditorPaneVisible(true);
        await selectFile(path);
        if (typeof document !== "undefined") {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              document.getElementById("blobert-editor-column")?.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
                inline: "nearest",
              });
            });
          });
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setNavError(msg);
      } finally {
        setBusy(false);
      }
    },
    [selectFile, setEditorPaneVisible],
  );

  return (
    <div style={s.bar}>
      <div style={s.row}>
        <button
          type="button"
          style={{
            ...s.btnPrimary,
            ...(modelTarget && !busy ? {} : { ...s.btnDisabled }),
          }}
          disabled={!modelTarget || busy}
          title={modelTarget?.description ?? "Not available for this command"}
          onClick={() => openPath(modelTarget?.path)}
        >
          Model code
        </button>
        <button
          type="button"
          style={{
            ...s.btnPrimary,
            ...(animTarget && !busy ? {} : { ...s.btnDisabled }),
          }}
          disabled={!animTarget || busy}
          title={
            animTarget
              ? `${animTarget.description} — opens Blender Python in the center editor (Monaco). Click the vertical “Code” strip if the editor is hidden.`
              : "Not available for this command"
          }
          onClick={() => openPath(animTarget?.path)}
        >
          Animation code
        </button>
        <span style={s.hint}>
          Opens Python in the center editor — cmd: <code style={{ color: "#bbb" }}>{cmd}</code>
          {enemy ? (
            <>
              {" "}
              · target:{" "}
              <code style={{ color: "#bbb" }} title={enemy}>
                {enemySelectOptionLabel(cmd, enemy, animatedEnemyMeta)}
              </code>
            </>
          ) : null}
        </span>
      </div>
      {animTarget && animExtras.length > 0 ? (
        <div style={s.row}>
          <span style={s.hint}>More animation:</span>
          {animExtras.map((t) => (
            <button
              key={t.path}
              type="button"
              style={{ ...s.btnSmall, ...(busy ? s.btnDisabled : {}) }}
              disabled={busy}
              title={t.description}
              onClick={() => openPath(t.path)}
            >
              {shortLabelForAnimationExtra(t.path)}
            </button>
          ))}
        </div>
      ) : null}
      <div style={s.row}>
        <button type="button" style={s.treeToggle} onClick={() => setPartsOpen((o) => !o)}>
          {partsOpen ? "▼" : "▶"} Mesh parts (source)
        </button>
      </div>
      {partsOpen ? (
        <div style={s.tree}>
          <PartTreeRows nodes={partTree} depth={0} />
        </div>
      ) : null}
      {navError ? <div style={s.err}>{navError}</div> : null}
    </div>
  );
}
