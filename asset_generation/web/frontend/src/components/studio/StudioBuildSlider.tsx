import type { CSSProperties } from "react";
import { coerceFloatControlValue } from "../Preview/BuildControlRow";
import type { AnimatedBuildControlDef } from "../../types";
import { STUDIO_INK_MUTED } from "../../styles/studioTokens";
import { studioBuildSliderLabel, studioBuildSliderValue } from "./studioBuildStyles";

type Props = {
  def: Extract<AnimatedBuildControlDef, { type: "float" }>;
  value: unknown;
  accentHue: string;
  disabled?: boolean;
  showHint?: boolean;
  onChange: (v: number) => void;
};

function formatSliderValue(n: number, step: number): string {
  if (step >= 1) return String(Math.round(n));
  if (step >= 0.05) return n.toFixed(2).replace(/\.?0+$/, "");
  return n.toFixed(3).replace(/\.?0+$/, "");
}

function formatRange(min: number, max: number, step: number): string {
  const fmt = (x: number) => (step >= 1 ? String(Math.round(x)) : x.toFixed(1).replace(/\.0$/, ""));
  return `${fmt(min)}–${fmt(max)}`;
}

const trackShell: CSSProperties = {
  position: "relative",
  height: 12,
  display: "flex",
  alignItems: "center",
  flex: 1,
  minWidth: 0,
};

const track: CSSProperties = {
  position: "absolute",
  left: 0,
  right: 0,
  height: 4,
  background: "#1d1d26",
  borderRadius: 2,
};

const numberInputStyle: CSSProperties = {
  width: 52,
  flexShrink: 0,
  fontSize: 11,
  fontWeight: 600,
  color: "#ededf0",
  background: "#16161d",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "4px 6px",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
};

export function StudioBuildSlider({ def, value, accentHue, disabled, showHint = true, onChange }: Props) {
  const n = coerceFloatControlValue(value, def.default);
  const span = def.max - def.min;
  const pct = span > 0 ? ((n - def.min) / span) * 100 : 0;
  const clampedPct = Math.min(100, Math.max(0, pct));
  const unit = def.unit?.trim() ?? "";

  function commit(raw: number) {
    const clamped = Math.min(def.max, Math.max(def.min, raw));
    onChange(clamped);
  }

  return (
    <div
      style={{ marginBottom: 12, opacity: disabled ? 0.42 : 1, pointerEvents: disabled ? "none" : undefined }}
      data-testid={`studio-build-slider-${def.key}`}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, gap: 8 }}>
        <span style={studioBuildSliderLabel} title={def.key}>
          {def.label}
        </span>
        <span style={studioBuildSliderValue}>
          <span>{formatSliderValue(n, def.step)}</span>
          <span style={{ marginLeft: 6, color: STUDIO_INK_MUTED }}>{formatRange(def.min, def.max, def.step)}</span>
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={trackShell}>
          <div style={track} aria-hidden>
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                bottom: 0,
                width: `${clampedPct}%`,
                background: accentHue,
                borderRadius: 2,
              }}
            />
          </div>
          <div
            aria-hidden
            style={{
              position: "absolute",
              left: `calc(${clampedPct}% - 6px)`,
              top: 0,
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: accentHue,
              boxShadow: "0 1px 3px rgba(0,0,0,0.4)",
              pointerEvents: "none",
            }}
          />
          <input
            type="range"
            min={def.min}
            max={def.max}
            step={def.step}
            value={n}
            disabled={disabled}
            aria-label={def.label}
            style={{
              position: "relative",
              width: "100%",
              height: 12,
              margin: 0,
              opacity: 0,
              cursor: disabled ? "not-allowed" : "pointer",
            }}
            onChange={(e) => commit(Number(e.target.value))}
          />
        </div>
        <input
          type="number"
          min={def.min}
          max={def.max}
          step={def.step}
          value={n}
          disabled={disabled}
          aria-label={`${def.label} value`}
          style={numberInputStyle}
          onChange={(e) => {
            const parsed = Number(e.target.value);
            if (Number.isFinite(parsed)) commit(parsed);
          }}
        />
        {unit ? (
          <span
            style={{
              fontSize: 10,
              color: STUDIO_INK_MUTED,
              minWidth: 52,
              flexShrink: 0,
              textAlign: "right",
            }}
          >
            {unit}
          </span>
        ) : null}
      </div>
      {showHint && def.hint ? (
        <div style={{ fontSize: 10, color: STUDIO_INK_MUTED, marginTop: 4, lineHeight: 1.35 }}>{def.hint}</div>
      ) : null}
    </div>
  );
}
