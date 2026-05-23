import type { ColorPickerValue } from "../ColorPicker/ColorPickerTabs";
import { StudioSwatch } from "./StudioSwatch";

type Props = {
  colors: readonly string[];
  value: ColorPickerValue;
  onPick: (hex: string) => void;
  size?: number;
};

export function StudioPaletteRow({ colors, value, onPick, size = 24 }: Props) {
  if (colors.length === 0) return null;

  return (
    <div
      data-testid="studio-palette-row"
      style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}
    >
      {colors.map((c) => (
        <StudioSwatch
          key={c}
          color={c}
          size={size}
          selected={value.type === "single" && value.color.toLowerCase() === c.replace(/^#/, "").toLowerCase()}
          onClick={() => onPick(c)}
          title={c}
        />
      ))}
    </div>
  );
}
