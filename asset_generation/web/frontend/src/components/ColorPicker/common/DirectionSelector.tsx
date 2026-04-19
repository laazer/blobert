import { colorPickerStyles } from "../colorPickerStyles";

export type GradientDirection = "horizontal" | "vertical" | "radial";

export interface DirectionSelectorProps {
  direction: GradientDirection;
  onChange: (direction: GradientDirection) => void;
  disabled?: boolean;
}

/**
 * Direction selector for gradients.
 * Renders a segmented control with three options: horizontal, vertical, radial.
 */
export function DirectionSelector({
  direction,
  onChange,
  disabled = false,
}: DirectionSelectorProps) {
  const directions: GradientDirection[] = ["horizontal", "vertical", "radial"];

  return (
    <div style={colorPickerStyles.directionRow}>
      <div style={colorPickerStyles.hexLabel}>Direction</div>
      <div
        style={colorPickerStyles.directionButtonGroup}
        role="group"
        aria-label="Gradient direction"
      >
        {directions.map((d, i) => (
          <button
            key={d}
            disabled={disabled}
            aria-pressed={direction === d}
            onClick={() => onChange(d)}
            style={{
              ...colorPickerStyles.directionButton(
                direction === d,
                i === 0 ? "left" : i === directions.length - 1 ? "right" : "middle"
              ),
              opacity: disabled ? 0.5 : 1,
              pointerEvents: disabled ? "none" : "auto",
            }}
          >
            {d === "horizontal"
              ? "→"
              : d === "vertical"
                ? "↓"
                : "◯"}
          </button>
        ))}
      </div>
    </div>
  );
}
