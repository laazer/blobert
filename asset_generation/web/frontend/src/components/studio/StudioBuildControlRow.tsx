import type { AnimatedBuildControlDef } from "../../types";
import { studioBuildRowLabel, studioBuildSegmentTrack } from "./studioBuildStyles";
import { StudioBuildEyeCountRow } from "./StudioBuildEyeCountRow";
import { StudioBuildHexRow } from "./StudioBuildHexRow";
import { StudioBuildSegmentedRow } from "./StudioBuildSegmentedRow";
import { StudioBuildSelectRow } from "./StudioBuildSelectRow";
import { StudioBuildSlider } from "./StudioBuildSlider";
import { StudioBuildToggle } from "./StudioBuildToggle";

/** Segmented pills up to this many options; wider lists use a studio-styled select. */
const STUDIO_SEGMENTED_MAX = 12;

type Props = {
  def: AnimatedBuildControlDef;
  value: unknown;
  accentHue: string;
  disabled?: boolean;
  onChange: (v: number | string | boolean) => void;
};

function isHexStrDef(def: AnimatedBuildControlDef): boolean {
  if (def.type !== "str") return false;
  return (
    def.key.endsWith("_hex") ||
    def.key.endsWith("_color_hex") ||
    (def.key.includes("_texture_") && def.key.includes("color"))
  );
}

function useSegmentedForSelectStr(def: Extract<AnimatedBuildControlDef, { type: "select_str" }>): boolean {
  if (def.segmented && def.options.length === 2) return true;
  return def.options.length > 0 && def.options.length <= STUDIO_SEGMENTED_MAX;
}

export function StudioBuildControlRow({ def, value, accentHue, disabled, onChange }: Props) {
  if (def.key === "eye_count") {
    return (
      <StudioBuildEyeCountRow
        def={def}
        value={value}
        accentHue={accentHue}
        disabled={disabled}
        onChange={(v) => onChange(v)}
      />
    );
  }

  if (def.type === "float") {
    return (
      <StudioBuildSlider def={def} value={value} accentHue={accentHue} disabled={disabled} onChange={onChange} />
    );
  }

  if (def.type === "bool") {
    const b = typeof value === "boolean" ? value : def.default;
    if (def.key.endsWith("_enabled")) {
      return (
        <StudioBuildToggle
          label={def.label}
          controlKey={def.key}
          checked={b}
          accentHue={accentHue}
          disabled={disabled}
          onChange={(v) => onChange(v)}
        />
      );
    }
    return (
      <StudioBuildSegmentedRow
        label={def.label}
        controlKey={def.key}
        accentHue={accentHue}
        disabled={disabled}
        value={b}
        options={[
          { value: false, label: "off" },
          { value: true, label: "on" },
        ]}
        onChange={(v) => onChange(v)}
      />
    );
  }

  if (def.type === "select") {
    const n = typeof value === "number" ? value : def.default;
    if (def.options.length <= STUDIO_SEGMENTED_MAX) {
      const sorted = [...def.options].sort((a, b) => a - b);
      return (
        <StudioBuildSegmentedRow
          label={def.label}
          controlKey={def.key}
          accentHue={accentHue}
          disabled={disabled}
          value={n}
          options={sorted.map((opt) => ({ value: opt, label: String(opt) }))}
          onChange={(v) => onChange(v)}
        />
      );
    }
    return (
      <StudioBuildSelectRow
        label={def.label}
        controlKey={def.key}
        value={String(n)}
        options={def.options.map(String)}
        disabled={disabled}
        onChange={(v) => onChange(Number(v))}
      />
    );
  }

  if (def.type === "select_str") {
    const strVal = typeof value === "string" ? value : def.default;
    if (useSegmentedForSelectStr(def)) {
      return (
        <StudioBuildSegmentedRow
          label={def.label}
          controlKey={def.key}
          accentHue={accentHue}
          disabled={disabled}
          value={strVal}
          options={def.options.map((opt) => ({ value: opt, label: opt }))}
          onChange={(v) => onChange(v)}
        />
      );
    }
    return (
      <StudioBuildSelectRow
        label={def.label}
        controlKey={def.key}
        value={strVal}
        options={def.options}
        disabled={disabled}
        onChange={(v) => onChange(v)}
      />
    );
  }

  if (def.type === "int") {
    const n = typeof value === "number" ? value : def.default;
    return (
      <StudioBuildSlider
        def={{
          key: def.key,
          label: def.label,
          type: "float",
          min: def.min,
          max: def.max,
          step: 1,
          default: n,
        }}
        value={n}
        accentHue={accentHue}
        disabled={disabled}
        onChange={(v) => onChange(Math.round(v))}
      />
    );
  }

  if (def.type === "str" && isHexStrDef(def)) {
    const strVal = typeof value === "string" ? value : String(def.default ?? "");
    return (
      <StudioBuildHexRow
        label={def.label}
        controlKey={def.key}
        value={strVal}
        disabled={disabled}
        onChange={(v) => onChange(v)}
      />
    );
  }

  if (def.type === "str") {
    const strVal = typeof value === "string" ? value : String(def.default ?? "");
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          opacity: disabled ? 0.42 : 1,
          pointerEvents: disabled ? "none" : undefined,
        }}
      >
        <div style={studioBuildRowLabel}>{def.label}</div>
        <div style={{ ...studioBuildSegmentTrack, flex: 1, maxWidth: 220 }}>
          <input
            type="text"
            value={strVal}
            disabled={disabled}
            spellCheck={false}
            aria-label={def.label}
            style={{
              width: "100%",
              border: 0,
              background: "transparent",
              color: "#ededf0",
              fontSize: 11,
              fontWeight: 600,
              padding: "4px 8px",
            }}
            onChange={(e) => onChange(e.target.value)}
          />
        </div>
      </div>
    );
  }

  return null;
}
