import { useState } from "react";
import type { AnimatedBuildControlDef } from "../../types";
import { readHexFromClipboard } from "../../utils/clipboardHex";

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

function hexForColorInput(raw: string): string {
  const h = (raw || "").replace(/^#/, "").trim();
  if (/^[0-9a-fA-F]{6}$/.test(h)) return `#${h.toLowerCase()}`;
  return "#6b6b6b";
}

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
  const rs = rowStyles;
  const strVal = typeof value === "string" ? value : String(def.default ?? "");
  const [pasteHint, setPasteHint] = useState<string | null>(null);
  const sanitizeHex = (raw: string) =>
    raw.replace(/^#/, "").replace(/[^0-9a-fA-F]/g, "").slice(0, 6).toLowerCase();

  async function pasteColor() {
    const parsed = await readHexFromClipboard();
    if (parsed) {
      onChange(parsed);
      setPasteHint(null);
    } else {
      setPasteHint("No #RRGGBB in clipboard");
      window.setTimeout(() => setPasteHint(null), 2000);
    }
  }

  return (
    <label style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap", maxWidth: "100%" }}>
      <span style={rs.label}>{def.label}</span>
      <input
        style={{ ...rs.select, width: 28, height: 22, padding: 0, cursor: "pointer" }}
        type="color"
        value={hexForColorInput(strVal)}
        title="Pick color (fills hex field)"
        onChange={(e) => onChange(e.target.value.replace(/^#/, "").toLowerCase())}
      />
      <input
        style={{ ...rs.input, width: 80, flex: "1 1 72px" }}
        type="text"
        placeholder="RRGGBB"
        value={strVal}
        onChange={(e) => onChange(e.target.value)}
        onBlur={(e) => {
          const v = e.target.value;
          const t = sanitizeHex(v);
          if (t !== v) onChange(t);
        }}
        spellCheck={false}
      />
      <button type="button" style={pasteBtnStyle} title="Paste #RRGGBB or RRGGBB from clipboard" onClick={() => void pasteColor()}>
        Paste color
      </button>
      {pasteHint ? (
        <span style={{ fontSize: 10, color: "#f48771", width: "100%" }} role="status">
          {pasteHint}
        </span>
      ) : null}
    </label>
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
    if (def.key.endsWith("_hex")) {
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
  const n = typeof value === "number" ? value : def.default;
  return (
    <label
      style={{
        display: "flex",
        gap: 6,
        alignItems: "center",
        flexWrap: "wrap",
        maxWidth: "100%",
      }}
    >
      <span style={rs.label} title={def.key}>
        {def.label}
      </span>
      <input
        type="range"
        min={def.min}
        max={def.max}
        step={def.step}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={def.label}
        style={{ flex: "1 1 72px", minWidth: 72, maxWidth: 160 }}
      />
      <input
        style={rs.inputFloat}
        type="number"
        step={def.step}
        min={def.min}
        max={def.max}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
