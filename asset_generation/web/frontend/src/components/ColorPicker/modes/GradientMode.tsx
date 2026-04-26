import { HexInput } from "../common/HexInput";
import { DirectionSelector, type GradientDirection } from "../common/DirectionSelector";
import { colorPickerStyles } from "../colorPickerStyles";

export interface GradientModeProps {
  colorA: string; // 6-char hex without #
  colorB: string; // 6-char hex without #
  direction: GradientDirection;
  onChange?: (colorA: string, colorB: string, direction: GradientDirection) => void;
  onColorAChange?: (color: string) => void;
  onColorBChange?: (color: string) => void;
  onDirectionChange?: (direction: GradientDirection) => void;
  disabled?: boolean;
}

/**
 * Gradient color picker mode with two color circles and direction selector.
 * Supports both individual callbacks and unified onChange for flexibility.
 */
export function GradientMode({
  colorA,
  colorB,
  direction,
  onChange,
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

  const handleColorAChange = (color: string) => {
    onColorAChange?.(color);
    if (onChange) onChange(color, colorB, direction);
  };

  const handleColorBChange = (color: string) => {
    onColorBChange?.(color);
    if (onChange) onChange(colorA, color, direction);
  };

  const handleDirectionChange = (dir: GradientDirection) => {
    onDirectionChange?.(dir);
    if (onChange) onChange(colorA, colorB, dir);
  };

  return (
    <div style={colorPickerStyles.modeContent}>
      <HexInput
        value={colorA}
        onChange={handleColorAChange}
        disabled={disabled}
        label="From Color"
        onCopyClick={handleCopyClick}
      />

      <HexInput
        value={colorB}
        onChange={handleColorBChange}
        disabled={disabled}
        label="To Color"
        onCopyClick={handleCopyClick}
      />

      <DirectionSelector
        direction={direction}
        onChange={handleDirectionChange}
        disabled={disabled}
      />
    </div>
  );
}
