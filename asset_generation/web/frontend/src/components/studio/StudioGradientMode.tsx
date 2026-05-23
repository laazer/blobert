import type { GradientDirection } from "../ColorPicker/common/DirectionSelector";
import { studioLabelCaps, studioPillStyle } from "./studioFillStyles";
import { StudioHexRow } from "./StudioHexRow";

export type StudioGradientModeProps = {
  colorA: string;
  colorB: string;
  direction: GradientDirection;
  onChange: (colorA: string, colorB: string, direction: GradientDirection) => void;
  paletteColors?: readonly string[];
  disabled?: boolean;
};

const DIRECTION_OPTIONS: { id: GradientDirection; label: string }[] = [
  { id: "horizontal", label: "linear" },
  { id: "radial", label: "radial" },
  { id: "vertical", label: "vertical" },
];

function hexWithHash(raw: string): string {
  const t = raw.trim().replace(/^#/, "");
  return t ? `#${t}` : "#000000";
}

function stripHash(hex: string): string {
  return hex.trim().replace(/^#/, "").toLowerCase();
}

function gradientPreviewCss(colorA: string, colorB: string, direction: GradientDirection): string {
  const a = hexWithHash(colorA);
  const b = hexWithHash(colorB);
  if (direction === "vertical") return `linear-gradient(180deg, ${a}, ${b})`;
  if (direction === "radial") return `radial-gradient(circle at center, ${a}, ${b})`;
  return `linear-gradient(135deg, ${a}, ${b})`;
}

type StopProps = {
  index: 0 | 1;
  hex: string;
  paletteColors: readonly string[];
  onPick: (hex: string) => void;
  disabled?: boolean;
};

function GradientStop({ index, hex, paletteColors, onPick, disabled }: StopProps) {
  return (
    <div style={{ flex: 1 }}>
      <div style={studioLabelCaps}>Stop {index + 1}</div>
      <div style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
        {paletteColors.slice(0, 5).map((c) => {
          const selected = stripHash(hex) === stripHash(c);
          return (
            <button
              key={c}
              type="button"
              disabled={disabled}
              title={c}
              aria-label={`Stop ${index + 1} ${c}`}
              onClick={() => onPick(c)}
              style={{
                width: 18,
                height: 18,
                borderRadius: 4,
                padding: 0,
                background: c,
                border: selected ? "2px solid #fff" : "1px solid rgba(255,255,255,0.1)",
                cursor: disabled ? "not-allowed" : "pointer",
              }}
            />
          );
        })}
      </div>
      <StudioHexRow color={hex} onChange={onPick} disabled={disabled} />
    </div>
  );
}

/** Studio Look gradient fill (redesign_v2). */
export function StudioGradientMode({
  colorA,
  colorB,
  direction,
  onChange,
  paletteColors = [],
  disabled = false,
}: StudioGradientModeProps) {
  const swatches = paletteColors.length > 0 ? paletteColors : ["#888888", "#aaaaaa"];

  return (
    <div
      style={{ display: "flex", flexDirection: "column", gap: 8 }}
      data-testid="studio-gradient-mode"
    >
      <div
        style={{
          height: 40,
          borderRadius: 7,
          background: gradientPreviewCss(colorA, colorB, direction),
          boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.06)",
        }}
      />
      <div style={{ display: "flex", gap: 8 }}>
        <GradientStop
          index={0}
          hex={colorA}
          paletteColors={swatches}
          disabled={disabled}
          onPick={(c) => onChange(stripHash(c), colorB, direction)}
        />
        <GradientStop
          index={1}
          hex={colorB}
          paletteColors={swatches}
          disabled={disabled}
          onPick={(c) => onChange(colorA, stripHash(c), direction)}
        />
      </div>
      <div style={{ display: "flex", gap: 4 }}>
        {DIRECTION_OPTIONS.map((opt) => (
          <button
            key={opt.id}
            type="button"
            disabled={disabled}
            aria-pressed={direction === opt.id}
            data-testid={`studio-gradient-dir-${opt.id}`}
            onClick={() => onChange(colorA, colorB, opt.id)}
            style={studioPillStyle(direction === opt.id)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
