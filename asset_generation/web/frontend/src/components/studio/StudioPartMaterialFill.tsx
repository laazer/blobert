import { useCallback, useMemo } from "react";
import { useAppStore } from "../../store/useAppStore";
import { StudioColorPickerTabs } from "./StudioColorPickerTabs";
import { studioFillPanelStyle } from "./studioFillStyles";
import {
  buildColorPickerValue,
  carryFillPaletteOnModeChange,
  colorPickerValueToStoreUpdates,
  normalizedFillMode,
  partMaterialKeys,
} from "../../utils/zoneColorPickerBridge";

type Props = {
  slug: string;
  materialPrefix: string;
  legacyHexKey: string;
  accentHue: string;
  paletteColors?: readonly string[];
  embedded?: boolean;
  testId?: string;
};

/**
 * Studio color / gradient / image fill for extras and per-limb/joint material overrides.
 */
export function StudioPartMaterialFill({
  slug,
  materialPrefix,
  legacyHexKey,
  accentHue,
  paletteColors,
  embedded,
  testId,
}: Props) {
  const values = useAppStore((s) => s.animatedBuildOptionValues[slug] ?? {});
  const setOption = useAppStore((s) => s.setAnimatedBuildOption);
  const applyBulk = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);

  const keys = useMemo(
    () => partMaterialKeys(materialPrefix, legacyHexKey),
    [materialPrefix, legacyHexKey],
  );
  const modeKey = `${materialPrefix}_mode`;
  const colorMode = normalizedFillMode(materialPrefix, values);
  const pickerValue = buildColorPickerValue(colorMode, values, keys);

  const updateMode = useCallback(
    (nextMode: "single" | "gradient" | "image") => {
      if (nextMode !== "image" && colorMode !== "image") {
        const carry = carryFillPaletteOnModeChange(
          materialPrefix,
          colorMode,
          nextMode,
          values,
        );
        setOption(slug, modeKey, nextMode);
        if (Object.keys(carry).length > 0) applyBulk(slug, carry);
        return;
      }
      setOption(slug, modeKey, nextMode);
    },
    [slug, materialPrefix, colorMode, values, setOption, applyBulk, modeKey],
  );

  const onChange = useCallback(
    (v: typeof pickerValue) => {
      const updates = colorPickerValueToStoreUpdates(v, keys);
      if (Object.keys(updates).length > 0) {
        applyBulk(slug, updates);
      }
      if (v.type === "single" && legacyHexKey) {
        setOption(slug, legacyHexKey, v.color.replace(/^#/, ""));
      }
    },
    [slug, keys, applyBulk, legacyHexKey, setOption],
  );

  const onPalettePick = useCallback(
    (pickHex: string) => {
      const normalized = pickHex.replace(/^#/, "");
      if (keys.hexKey) setOption(slug, keys.hexKey, normalized);
      if (legacyHexKey) setOption(slug, legacyHexKey, normalized);
    },
    [slug, keys.hexKey, legacyHexKey, setOption],
  );

  return (
    <div
      data-testid={testId ?? `studio-part-material-fill-${materialPrefix}`}
      style={studioFillPanelStyle(embedded)}
    >
      <StudioColorPickerTabs
        accentHue={accentHue}
        mode={pickerValue.type}
        value={pickerValue}
        paletteColors={paletteColors}
        onPaletteColorPick={paletteColors?.length ? onPalettePick : undefined}
        onModeChange={updateMode}
        onChange={onChange}
      />
    </div>
  );
}
