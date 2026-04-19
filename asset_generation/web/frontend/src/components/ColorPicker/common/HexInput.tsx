import { colorPickerStyles } from "../colorPickerStyles";
import { hexForColorInput, sanitizeHex } from "../../../utils/clipboardHex";

export interface HexInputProps {
  value: string; // 6-char hex without #
  onChange: (value: string) => void;
  disabled?: boolean;
  label?: string;
  onCopyClick?: (hex: string) => void;
}

/**
 * Reusable hex color input field with validation and optional color swatch.
 * - Accepts hex input with or without #
 * - Validates on blur, sanitizes invalid values
 * - Stores value as 6-char lowercase hex without #
 * - Displays as #RRGGBB in the input using hexForColorInput utility
 */
export function HexInput({
  value,
  onChange,
  disabled = false,
  label,
  onCopyClick,
}: HexInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let v = e.target.value;
    // Remove # if user typed it
    if (v.startsWith("#")) {
      v = v.slice(1);
    }
    // Allow partial input while typing
    onChange(v.toLowerCase());
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const sanitized = sanitizeHex(e.target.value);
    onChange(sanitized);
  };

  const handleColorInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // HTML5 color input returns #RRGGBB, convert to RRGGBB
    const hex = e.target.value.replace(/^#/, "").toLowerCase();
    onChange(hex);
  };

  const swatchStyle = {
    ...colorPickerStyles.colorSwatch,
    backgroundColor: `#${value || "000000"}`,
  };

  return (
    <div>
      {label && <div style={colorPickerStyles.hexLabel}>{label}</div>}
      <div style={colorPickerStyles.hexInputRow}>
        {/* HTML5 color input for visual picker */}
        <input
          type="color"
          value={hexForColorInput(value)}
          onChange={handleColorInputChange}
          disabled={disabled}
          title="Pick color"
          style={{
            ...swatchStyle,
            padding: 0,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        />

        {/* Text input for hex code */}
        <input
          type="text"
          placeholder="RRGGBB"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          spellCheck={false}
          style={{
            ...colorPickerStyles.hexInput,
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? "not-allowed" : "text",
          }}
        />

        {/* Copy button (optional) */}
        {onCopyClick && (
          <button
            title="Copy hex to clipboard"
            disabled={disabled}
            onClick={() => onCopyClick(value)}
            style={{
              background: "#3c3c3c",
              color: "#d4d4d4",
              border: "1px solid #555555",
              borderRadius: 3,
              padding: "2px 4px",
              fontSize: 11,
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: disabled ? 0.5 : 1,
            }}
          >
            Copy
          </button>
        )}
      </div>
    </div>
  );
}
