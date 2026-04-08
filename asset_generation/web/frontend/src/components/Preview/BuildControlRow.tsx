import type { AnimatedBuildControlDef } from "../../types";

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

export function ControlRow({
  def,
  value,
  onChange,
}: {
  def: AnimatedBuildControlDef;
  value: unknown;
  onChange: (v: number | string) => void;
}) {
  const rs = rowStyles;
  if (def.type === "float") {
    return <FloatRow def={def} value={value} onChange={onChange} />;
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
  if (def.type === "string") {
    const strVal = typeof value === "string" ? value : def.default;
    const isHexSlot = def.key.endsWith("_hex");
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap", maxWidth: "100%" }}>
        <span style={rs.label}>{def.label}</span>
        {isHexSlot ? (
          <input
            style={{ ...rs.select, width: 28, height: 22, padding: 0, cursor: "pointer" }}
            type="color"
            value={hexForColorInput(strVal)}
            title="Pick color (fills hex field)"
            onChange={(e) => onChange(e.target.value.replace(/^#/, "").toLowerCase())}
          />
        ) : null}
        <input
          style={{ ...rs.input, width: isHexSlot ? 80 : 88, flex: "1 1 72px" }}
          type="text"
          placeholder={isHexSlot ? "RRGGBB" : ""}
          value={strVal}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
        />
      </label>
    );
  }
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
