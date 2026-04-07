import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { animatedExportRelativePath } from "../../utils/glbVariants";

const s = {
  bar: {
    background: "#1e1e1e",
    borderBottom: "1px solid #3c3c3c",
    padding: "4px 8px",
    display: "flex",
    gap: 8,
    alignItems: "center",
    flexWrap: "wrap",
    flexShrink: 0,
  },
  label: { color: "#9d9d9d", fontSize: 11 },
  select: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
  },
  input: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 56,
  },
} as const;

function ControlRow({
  def,
  value,
  onChange,
}: {
  def: AnimatedBuildControlDef;
  value: unknown;
  onChange: (v: number) => void;
}) {
  if (def.type === "select") {
    const n = typeof value === "number" ? value : def.default;
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <span style={s.label}>{def.label}</span>
        <select
          style={s.select}
          value={n}
          onChange={(e) => onChange(Number(e.target.value))}
        >
          {def.options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </label>
    );
  }
  const n = typeof value === "number" ? value : def.default;
  return (
    <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
      <span style={s.label}>{def.label}</span>
      <input
        style={s.input}
        type="number"
        min={def.min}
        max={def.max}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

/**
 * Procedural build options for the selected animated enemy (preview always uses variant index 00).
 */
export function BuildControls() {
  const commandContext = useAppStore((st) => st.commandContext);
  const animatedEnemyMeta = useAppStore((st) => st.animatedEnemyMeta);
  const animatedBuildControls = useAppStore((st) => st.animatedBuildControls);
  const animatedBuildOptionValues = useAppStore((st) => st.animatedBuildOptionValues);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);
  const selectAssetByPath = useAppStore((st) => st.selectAssetByPath);

  const { cmd, enemy } = commandContext;
  const isAnimatedEnemy =
    cmd === "animated" &&
    Boolean(enemy) &&
    enemy !== "all" &&
    animatedEnemyMeta.some((m) => m.slug === enemy);

  useEffect(() => {
    if (!isAnimatedEnemy) return;
    selectAssetByPath(animatedExportRelativePath(enemy, 0));
  }, [isAnimatedEnemy, enemy, selectAssetByPath]);

  if (!isAnimatedEnemy) {
    return null;
  }

  const defs = animatedBuildControls[enemy] ?? [];
  if (defs.length === 0) {
    return null;
  }

  const values = animatedBuildOptionValues[enemy] ?? {};

  return (
    <div style={s.bar}>
      <span style={s.label}>Build</span>
      {defs.map((def) => (
        <ControlRow
          key={def.key}
          def={def}
          value={values[def.key]}
          onChange={(v) => setAnimatedBuildOption(enemy, def.key, v)}
        />
      ))}
    </div>
  );
}
