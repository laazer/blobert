import { useEffect, useState, type CSSProperties } from "react";
import type { AnimatedBuildControlDef } from "../../types";
import { readHexFromClipboard } from "../../utils/clipboardHex";
import { ColorPickerUniversal, type ColorPickerValue } from "../ColorPicker/ColorPickerUniversal";

export const floatHintStyle = {
  fontSize: 10,
  color: "#858585",
  lineHeight: 1.35,
  maxWidth: 420,
} as const;

const floatTableRowBorder = { borderBottom: "1px solid #2a2a2a" } as const;

export const floatUnitStyle = { fontSize: 10, color: "#858585" } as const;

/** Match stored JSON / form values: accept finite numbers and numeric strings for float controls. */
export function coerceFloatControlValue(value: unknown, defaultValue: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return defaultValue;
}

export const rowStyles = {
  label: { color: "#9d9d9d", fontSize: 11 } as const,
  select: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
  } as const,
  input: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 56,
  } as const,
  inputFloat: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 64,
  } as const,
};

const pasteBtnStyle = {
  padding: "2px 8px",
  fontSize: 10,
  borderRadius: 3,
  cursor: "pointer" as const,
  border: "1px solid #555",
  background: "#3c3c3c",
  color: "#d4d4d4",
};

function HexStrControlRow({
  def,
  value,
  onChange,
}: {
  def: Extract<AnimatedBuildControlDef, { type: "str" }>;
  value: unknown;
  onChange: (v: string) => void;
}) {
  const strVal = typeof value === "string" ? value : String(def.default ?? "");
  const [pasteHint, setPasteHint] = useState<string | null>(null);
  const pickerValue: ColorPickerValue = { type: "single", color: strVal };

  // Cleanup timeout on unmount
  useEffect(() => {
    if (!pasteHint) return;
    const timeoutId = window.setTimeout(() => setPasteHint(null), 2000);
    return () => window.clearTimeout(timeoutId);
  }, [pasteHint]);

  async function pasteColor() {
    const parsed = await readHexFromClipboard();
    if (parsed) {
      onChange(parsed);
      setPasteHint(null);
    } else {
      setPasteHint("No #RRGGBB in clipboard");
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        alignItems: "flex-start",
        maxWidth: "100%",
      }}
    >
      <ColorPickerUniversal
        lockMode="single"
        mode="single"
        label={def.label}
        value={pickerValue}
        onChange={(v) => {
          if (v.type === "single") onChange(v.color);
        }}
        onModeChange={() => {}}
      />
      <button
        type="button"
        style={pasteBtnStyle}
        title="Paste #RRGGBB or RRGGBB from clipboard"
        onClick={() => void pasteColor()}
      >
        Paste color
      </button>
      {pasteHint ? (
        <span style={{ fontSize: 10, color: "#f48771", width: "100%" }} role="status">
          {pasteHint}
        </span>
      ) : null}
    </div>
  );
}

export function ControlRow({
  def,
  value,
  onChange,
}: {
  def: AnimatedBuildControlDef;
  value: unknown;
  onChange: (v: number | string | boolean) => void;
}) {
  const rs = rowStyles;
  if (def.type === "float") {
    return <FloatRow def={def} value={value} onChange={onChange} />;
  }
  if (def.type === "int") {
    const n = typeof value === "number" ? value : def.default;
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <span style={rs.label}>{def.label}</span>
        <input
          style={rs.input}
          type="number"
          min={def.min}
          max={def.max}
          value={n}
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </label>
    );
  }
  if (def.type === "select") {
    const n = typeof value === "number" ? value : def.default;
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <span style={rs.label}>{def.label}</span>
        <select
          style={rs.select}
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
  if (def.type === "select_str") {
    const strVal = typeof value === "string" ? value : def.default;
    if (def.segmented && def.options.length >= 2) {
      const n = def.options.length;
      return (
        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
          <span style={rs.label}>{def.label}</span>
          <div role="group" aria-label={def.label} style={{ display: "inline-flex" }}>
            {def.options.map((opt, i) => {
              const active = strVal === opt;
              const radiusLeft = i === 0 ? 3 : 0;
              const radiusRight = i === n - 1 ? 3 : 0;
              return (
                <button
                  key={opt}
                  type="button"
                  style={{
                    padding: "3px 10px",
                    fontSize: 11,
                    cursor: "pointer",
                    border: "1px solid #555",
                    marginLeft: i > 0 ? -1 : 0,
                    borderRadius: `${radiusLeft}px ${radiusRight}px ${radiusRight}px ${radiusLeft}px`,
                    background: active ? "#0e639c" : "#3c3c3c",
                    color: "#d4d4d4",
                    zIndex: active ? 1 : 0,
                  }}
                  aria-pressed={active}
                  onClick={() => onChange(opt)}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      );
    }
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap" }}>
        <span style={rs.label}>{def.label}</span>
        <select
          style={rs.select}
          value={strVal}
          onChange={(e) => onChange(e.target.value)}
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
  if (def.type === "bool") {
    const b = typeof value === "boolean" ? value : def.default;
    return (
      <label style={{ display: "flex", gap: 6, alignItems: "center", cursor: "pointer" }}>
        <input type="checkbox" checked={b} onChange={(e) => onChange(e.target.checked)} />
        <span style={rs.label}>{def.label}</span>
      </label>
    );
  }
  if (def.type === "str") {
    if (
      def.key.endsWith("_hex") ||
      (def.key.includes("_texture_") && def.key.includes("color"))
    ) {
      return <HexStrControlRow def={def} value={value} onChange={onChange} />;
    }
    const strVal = typeof value === "string" ? value : String(def.default ?? "");
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap", maxWidth: "100%" }}>
        <span style={rs.label}>{def.label}</span>
        <input
          style={{ ...rs.input, width: 88, flex: "1 1 72px" }}
          type="text"
          value={strVal}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
        />
      </label>
    );
  }
  return null;
}

/** One data row for Build tab Rig/Mesh float tables (must sit inside ``<tbody>``). */
export function FloatTableRow({
  def,
  value,
  onChange,
  disabled,
}: {
  def: Extract<AnimatedBuildControlDef, { type: "float" }>;
  value: unknown;
  onChange: (v: number) => void;
  disabled?: boolean;
}) {
  const rs = rowStyles;
  const n = coerceFloatControlValue(value, def.default);
  const unit = def.unit?.trim();
  return (
    <tr
      style={{
        opacity: disabled ? 0.42 : 1,
        pointerEvents: disabled ? "none" : undefined,
      }}
    >
      <td
        style={{
          ...floatTableRowBorder,
          ...rs.label,
          padding: "6px 10px 6px 0",
          verticalAlign: "top",
          minWidth: 100,
        }}
        title={def.key}
      >
        {def.label}
      </td>
      <td
        style={{
          ...floatTableRowBorder,
          padding: "6px 12px 6px 0",
          verticalAlign: "top",
          width: 1,
          whiteSpace: "nowrap",
        }}
      >
        <input
          style={rs.inputFloat}
          type="number"
          step={def.step}
          min={def.min}
          max={def.max}
          value={n}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-label={def.label}
        />
      </td>
      <td
        style={{
          ...floatTableRowBorder,
          ...floatUnitStyle,
          padding: "6px 12px 6px 0",
          verticalAlign: "top",
          width: 1,
          whiteSpace: "nowrap",
        }}
      >
        {unit || ""}
      </td>
      <td
        style={{
          ...floatTableRowBorder,
          fontSize: floatHintStyle.fontSize,
          color: floatHintStyle.color,
          lineHeight: floatHintStyle.lineHeight,
          padding: "6px 0 6px 0",
          verticalAlign: "top",
          wordBreak: "break-word",
        }}
      >
        {def.hint ?? ""}
      </td>
    </tr>
  );
}

/** Shared table chrome for Build Rig/Mesh and Extras zone float blocks. */
export const floatTableFrameStyle = {
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
    fontSize: 11,
  },
  th: {
    borderBottom: "1px solid #3c3c3c",
    color: "#858585",
    fontSize: 10,
    fontWeight: 600,
    padding: "4px 10px 8px 0",
    textAlign: "left" as const,
    verticalAlign: "bottom" as const,
  },
} as const;

export function FloatControlsTable({
  defs,
  values,
  onFloatChange,
  isRowDisabled,
  scrollWrapStyle,
}: {
  defs: Extract<AnimatedBuildControlDef, { type: "float" }>[];
  values: Readonly<Record<string, unknown>>;
  onFloatChange: (key: string, v: number) => void;
  isRowDisabled: (key: string) => boolean;
  /** When omitted, only horizontal overflow is clipped (e.g. Extras in-page scroll). */
  scrollWrapStyle?: CSSProperties;
}) {
  if (defs.length === 0) return null;
  const th = floatTableFrameStyle.th;
  return (
    <div style={scrollWrapStyle ?? { overflowX: "auto" }}>
      <table style={floatTableFrameStyle.table}>
        <thead>
          <tr>
            <th scope="col" style={{ ...th, minWidth: 100 }}>
              Parameter
            </th>
            <th scope="col" style={{ ...th, width: 1, whiteSpace: "nowrap", paddingRight: 12 }}>
              Value
            </th>
            <th scope="col" style={{ ...th, width: 1, whiteSpace: "nowrap", paddingRight: 12 }}>
              Unit
            </th>
            <th scope="col" style={th}>
              Note
            </th>
          </tr>
        </thead>
        <tbody>
          {defs.map((def) => (
            <FloatTableRow
              key={def.key}
              def={def}
              value={values[def.key]}
              disabled={isRowDisabled(def.key)}
              onChange={(v) => onFloatChange(def.key, v)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FloatRow({
  def,
  value,
  onChange,
}: {
  def: Extract<AnimatedBuildControlDef, { type: "float" }>;
  value: unknown;
  onChange: (v: number) => void;
}) {
  const rs = rowStyles;
  const n = coerceFloatControlValue(value, def.default);
  const unit = def.unit?.trim();
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        alignItems: "flex-start",
        minWidth: 0,
        maxWidth: "100%",
      }}
    >
      <label
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          flexWrap: "wrap",
          width: "100%",
        }}
      >
        <span style={rs.label} title={def.key}>
          {def.label}
        </span>
        <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <input
            style={rs.inputFloat}
            type="number"
            step={def.step}
            min={def.min}
            max={def.max}
            value={n}
            onChange={(e) => onChange(Number(e.target.value))}
            aria-label={def.label}
          />
          {unit ? <span style={floatUnitStyle}>{unit}</span> : null}
        </span>
      </label>
      {def.hint ? <span style={floatHintStyle}>{def.hint}</span> : null}
    </div>
  );
}
