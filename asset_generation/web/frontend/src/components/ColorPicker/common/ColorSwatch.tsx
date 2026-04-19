import { colorPickerStyles } from "../colorPickerStyles";

export interface ColorSwatchProps {
  color: string; // 6-char hex without #
  disabled?: boolean;
  onClick?: () => void;
  label?: string;
}

/**
 * Simple visual color preview box.
 * Displays a hex color as a colored square. Optionally clickable.
 */
export function ColorSwatch({
  color,
  disabled = false,
  onClick,
  label,
}: ColorSwatchProps) {
  const swatchStyle = {
    ...colorPickerStyles.colorSwatch,
    backgroundColor: `#${color || "000000"}`,
    cursor: disabled ? "not-allowed" : onClick ? "pointer" : "default",
    opacity: disabled ? 0.5 : 1,
  };

  const content = (
    <>
      {label && <div style={colorPickerStyles.hexLabel}>{label}</div>}
      <div style={swatchStyle} />
    </>
  );

  if (onClick && !disabled) {
    return (
      <button
        onClick={onClick}
        style={{
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
        }}
      >
        {content}
      </button>
    );
  }

  return <div>{content}</div>;
}
