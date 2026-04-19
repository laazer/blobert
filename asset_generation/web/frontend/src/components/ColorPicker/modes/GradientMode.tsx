import { HexInput } from "../common/HexInput";
import { DirectionSelector, type GradientDirection } from "../common/DirectionSelector";
import { colorPickerStyles } from "../colorPickerStyles";

export interface GradientModeProps {
  colorA: string; // 6-char hex without #
  colorB: string; // 6-char hex without #
  direction: GradientDirection;
  onColorAChange: (color: string) => void;
  onColorBChange: (color: string) => void;
  onDirectionChange: (direction: GradientDirection) => void;
  disabled?: boolean;
}

/**
 * Gradient color picker mode.
 * Provides two hex input fields for color A and B, plus direction selector.
 * Emits individual changes for each field.
 */
export function GradientMode({
  colorA,
  colorB,
  direction,
  onColorAChange,
  onColorBChange,
  onDirectionChange,
  disabled = false,
}: GradientModeProps) {
  const handleCopyClick = async (hex: string) => {
    try {
      await navigator.clipboard.writeText(`#${hex.toUpperCase()}`);
    } catch {
      // Silently fail if clipboard not available
    }
  };

  return (
    <div style={colorPickerStyles.modeContent}>
      <HexInput
        value={colorA}
        onChange={onColorAChange}
        disabled={disabled}
        label="From Color"
        onCopyClick={handleCopyClick}
      />

      <HexInput
        value={colorB}
        onChange={onColorBChange}
        disabled={disabled}
        label="To Color"
        onCopyClick={handleCopyClick}
      />

      <DirectionSelector
        direction={direction}
        onChange={onDirectionChange}
        disabled={disabled}
      />
    </div>
  );
}
