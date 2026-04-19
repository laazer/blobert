import { colorPickerStyles } from "./colorPickerStyles";
import { SingleColorMode } from "./modes/SingleColorMode";
import { GradientMode } from "./modes/GradientMode";
import { ImageMode } from "./modes/ImageMode";

// Discriminated union for color picker values
export type ColorPickerValue =
  | { type: "single"; color: string } // "RRGGBB"
  | {
      type: "gradient";
      colorA: string;
      colorB: string;
      direction: "horizontal" | "vertical" | "radial";
    }
  | { type: "image"; file: File | null; preview?: string };

export interface ColorPickerUniversalProps {
  mode: "single" | "gradient" | "image";
  onModeChange: (mode: "single" | "gradient" | "image") => void;
  value: ColorPickerValue;
  onChange: (value: ColorPickerValue) => void;
  disabled?: boolean;
  label?: string;
}

/**
 * Universal color picker component supporting three modes:
 * - Single Color: standard hex color selection
 * - Gradient: two-color gradients with direction control
 * - Image Texture: file upload for custom textures
 *
 * Accepts value as a discriminated union to keep mode and data synchronized.
 * All interactions call onChange with the updated value.
 */
export function ColorPickerUniversal({
  mode,
  onModeChange,
  value,
  onChange,
  disabled = false,
  label,
}: ColorPickerUniversalProps) {
  return (
    <div style={colorPickerStyles.container}>
      {label && <div style={colorPickerStyles.hexLabel}>{label}</div>}

      {/* Mode tab selector */}
      <div style={colorPickerStyles.tabRow} role="group" aria-label="Color picker mode">
        {["single", "gradient", "image"].map((m) => (
          <button
            key={m}
            disabled={disabled}
            aria-pressed={mode === m}
            style={{
              ...colorPickerStyles.tabButton(mode === m),
              opacity: disabled ? 0.5 : 1,
              pointerEvents: disabled ? "none" : "auto",
            }}
            onClick={() => onModeChange(m as "single" | "gradient" | "image")}
          >
            {m === "single" ? "Color" : m === "gradient" ? "Gradient" : "Image"}
          </button>
        ))}
      </div>

      {/* Mode content */}
      <div style={colorPickerStyles.modeContent}>
        {/* Single color mode */}
        {mode === "single" && value.type === "single" && (
          <SingleColorMode
            color={value.color}
            onChange={(color) => onChange({ type: "single", color })}
            disabled={disabled}
          />
        )}

        {/* Gradient mode */}
        {mode === "gradient" && value.type === "gradient" && (
          <GradientMode
            colorA={value.colorA}
            colorB={value.colorB}
            direction={value.direction}
            onColorAChange={(colorA) =>
              onChange({
                type: "gradient",
                colorA,
                colorB: value.colorB,
                direction: value.direction,
              })
            }
            onColorBChange={(colorB) =>
              onChange({
                type: "gradient",
                colorA: value.colorA,
                colorB,
                direction: value.direction,
              })
            }
            onDirectionChange={(direction) =>
              onChange({
                type: "gradient",
                colorA: value.colorA,
                colorB: value.colorB,
                direction,
              })
            }
            disabled={disabled}
          />
        )}

        {/* Image mode */}
        {mode === "image" && value.type === "image" && (
          <ImageMode
            file={value.file}
            preview={value.preview}
            onFileChange={(file, preview) =>
              onChange({ type: "image", file, preview })
            }
            disabled={disabled}
          />
        )}
      </div>
    </div>
  );
}
