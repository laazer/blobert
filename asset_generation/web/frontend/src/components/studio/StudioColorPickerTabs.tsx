import type { ColorPickerValue } from "../ColorPicker/ColorPickerTabs";
export type { ColorPickerValue };
import { StudioGradientMode } from "./StudioGradientMode";
import { StudioImageMode } from "./StudioImageMode";
import { StudioHexRow } from "./StudioHexRow";
import { StudioPaletteRow } from "./StudioPaletteRow";
import {
  studioFillContentStyle,
  studioFillRootStyle,
  studioFillTabBarStyle,
  studioFillTabStyle,
} from "./studioFillStyles";

const FILL_MODES = ["single", "gradient", "image"] as const;
type FillMode = (typeof FILL_MODES)[number];

const TAB_LABELS: Record<FillMode, string> = {
  single: "Color",
  gradient: "Gradient",
  image: "Image",
};

export type StudioColorPickerTabsProps = {
  mode: FillMode;
  onModeChange: (mode: FillMode) => void;
  value: ColorPickerValue;
  onChange: (value: ColorPickerValue) => void;
  accentHue: string;
  disabled?: boolean;
  paletteColors?: readonly string[];
  onPaletteColorPick?: (hex: string) => void;
};

/**
 * Studio Look fill control — Color / Gradient / Image (redesign_v2).
 * Separate from legacy ``ColorPickerTabs`` (IDE chrome).
 */
export function StudioColorPickerTabs({
  mode,
  onModeChange,
  value,
  onChange,
  accentHue,
  disabled = false,
  paletteColors,
  onPaletteColorPick,
}: StudioColorPickerTabsProps) {
  const showPalette =
    mode === "single" && paletteColors && paletteColors.length > 0 && onPaletteColorPick;

  return (
    <div style={studioFillRootStyle} data-testid="studio-color-picker-tabs">
      <div style={studioFillTabBarStyle} role="tablist" aria-label="Fill type">
        {FILL_MODES.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={mode === tab}
            disabled={disabled}
            onClick={() => onModeChange(tab)}
            style={studioFillTabStyle(mode === tab, accentHue)}
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      {showPalette ? (
        <StudioPaletteRow colors={paletteColors} value={value} onPick={onPaletteColorPick} />
      ) : null}

      <div style={studioFillContentStyle}>
        {mode === "single" && value.type === "single" ? (
          <StudioHexRow
            color={value.color}
            onChange={(color) => onChange({ type: "single", color })}
            disabled={disabled}
          />
        ) : null}

        {mode === "gradient" && value.type === "gradient" ? (
          <StudioGradientMode
            colorA={value.colorA}
            colorB={value.colorB}
            direction={value.direction}
            paletteColors={paletteColors}
            onChange={(colorA, colorB, direction) =>
              onChange({ type: "gradient", colorA, colorB, direction })
            }
            disabled={disabled}
          />
        ) : null}

        {mode === "image" && value.type === "image" ? (
          <StudioImageMode
            accentHue={accentHue}
            file={value.file ?? null}
            preview={value.preview}
            assetId={value.assetId}
            uvRect={value.uvRect}
            onFileChange={(file, preview, assetId, uvRect) =>
              onChange({
                type: "image",
                file,
                preview,
                assetId,
                uvRect: uvRect !== undefined ? uvRect : value.uvRect,
              })
            }
            disabled={disabled}
          />
        ) : null}
      </div>
    </div>
  );
}
