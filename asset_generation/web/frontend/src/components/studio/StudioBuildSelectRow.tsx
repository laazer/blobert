import type { CSSProperties } from "react";
import { studioBuildRowLabel, studioBuildSegmentTrack } from "./studioBuildStyles";

const selectStyle: CSSProperties = {
  flex: 1,
  minWidth: 0,
  maxWidth: 220,
  fontSize: 11,
  fontWeight: 600,
  color: "#ededf0",
  background: "#121218",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "5px 8px",
  cursor: "pointer",
};

type Props = {
  label: string;
  controlKey: string;
  value: string;
  options: readonly string[];
  disabled?: boolean;
  onChange: (v: string) => void;
};

export function StudioBuildSelectRow({ label, controlKey, value, options, disabled, onChange }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        opacity: disabled ? 0.42 : 1,
        pointerEvents: disabled ? "none" : undefined,
      }}
      data-testid={`studio-build-select-${controlKey}`}
    >
      <div style={studioBuildRowLabel}>{label}</div>
      <div style={{ ...studioBuildSegmentTrack, flex: 1, maxWidth: 220, padding: 0 }}>
        <select
          aria-label={label}
          value={value}
          disabled={disabled}
          style={selectStyle}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
