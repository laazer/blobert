import { HexInput } from "../common/HexInput";

export interface SingleColorModeProps {
  color: string; // 6-char hex without #
  onChange: (color: string) => void;
  disabled?: boolean;
}

/**
 * Single color picker mode.
 * Provides a hex input field with visual color picker.
 * Emits hex color (6-char lowercase, no #) on changes.
 */
export function SingleColorMode({
  color,
  onChange,
  disabled = false,
}: SingleColorModeProps) {
  const handleCopyClick = async (hex: string) => {
    try {
      await navigator.clipboard.writeText(`#${hex.toUpperCase()}`);
    } catch {
      // Silently fail if clipboard not available
    }
  };

  return (
    <HexInput
      value={color}
      onChange={onChange}
      disabled={disabled}
      label="Color"
      onCopyClick={handleCopyClick}
    />
  );
}
