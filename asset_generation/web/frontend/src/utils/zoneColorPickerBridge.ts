import type { GradientDirection } from "../components/ColorPicker/common/DirectionSelector";
import type { ColorPickerValue } from "../components/ColorPicker/ColorPickerTabs";
import { parseImageUvRect, stringifyImageUvRect } from "../components/ColorPicker/imageUvRect";

export type PickerMode = "single" | "gradient" | "image";

export type ColorFieldKeys = {
  hexKey: string;
  colorAKey: string;
  colorBKey: string;
  colorDirKey: string;
  imageIdKey: string;
  imagePreviewKey: string;
  imageUvRectKey: string;
  legacySingleKey?: string;
};

function gradientDirectionFromStore(raw: unknown): GradientDirection {
  const s = typeof raw === "string" ? raw.trim().toLowerCase() : "";
  if (s === "vertical" || s === "radial" || s === "horizontal") return s;
  return "horizontal";
}

export function zoneBackgroundColorKeys(zone: string): ColorFieldKeys {
  return {
    hexKey: `feat_${zone}_color_hex`,
    colorAKey: `feat_${zone}_color_a`,
    colorBKey: `feat_${zone}_color_b`,
    colorDirKey: `feat_${zone}_color_direction`,
    imageIdKey: `feat_${zone}_color_image_id`,
    imagePreviewKey: `feat_${zone}_color_image_preview`,
    imageUvRectKey: `feat_${zone}_color_image_uv_rect`,
  };
}

export function zonePatternColorKeys(zone: string, colorField = "pattern"): ColorFieldKeys {
  const p = `feat_${zone}_texture_${colorField}`;
  return {
    hexKey: `${p}_hex`,
    colorAKey: `${p}_grad_a`,
    colorBKey: `${p}_grad_b`,
    colorDirKey: `${p}_grad_direction`,
    imageIdKey: `${p}_image_id`,
    imagePreviewKey: `${p}_image_preview`,
    imageUvRectKey: `${p}_image_uv_rect`,
    legacySingleKey: p,
  };
}

export function buildColorPickerValue(
  mode: PickerMode,
  values: Readonly<Record<string, unknown>>,
  keys: ColorFieldKeys,
): ColorPickerValue {
  const singleColor: string =
    typeof values[keys.hexKey] === "string"
      ? (values[keys.hexKey] as string)
      : keys.legacySingleKey && typeof values[keys.legacySingleKey] === "string"
        ? (values[keys.legacySingleKey] as string)
        : "";
  if (mode === "gradient") {
    return {
      type: "gradient",
      colorA: typeof values[keys.colorAKey] === "string" ? (values[keys.colorAKey] as string) : "",
      colorB: typeof values[keys.colorBKey] === "string" ? (values[keys.colorBKey] as string) : "",
      direction: gradientDirectionFromStore(values[keys.colorDirKey]),
    };
  }
  if (mode === "image") {
    return {
      type: "image",
      file: null,
      preview:
        typeof values[keys.imagePreviewKey] === "string"
          ? (values[keys.imagePreviewKey] as string)
          : undefined,
      assetId:
        typeof values[keys.imageIdKey] === "string" &&
        (values[keys.imageIdKey] as string).trim() !== ""
          ? (values[keys.imageIdKey] as string)
          : undefined,
      uvRect: parseImageUvRect(values[keys.imageUvRectKey]),
    };
  }
  return { type: "single", color: singleColor };
}

export function colorPickerValueToStoreUpdates(
  value: ColorPickerValue,
  keys: ColorFieldKeys,
): Record<string, string> {
  const out: Record<string, string> = {};
  if (value.type === "single") {
    out[keys.hexKey] = value.color;
    return out;
  }
  if (value.type === "gradient") {
    out[keys.colorAKey] = value.colorA;
    out[keys.colorBKey] = value.colorB;
    out[keys.colorDirKey] = value.direction;
    return out;
  }
  out[keys.imagePreviewKey] = value.preview ?? "";
  out[keys.imageIdKey] = value.assetId ?? "";
  out[keys.imageUvRectKey] = value.uvRect ? stringifyImageUvRect(value.uvRect) : "";
  return out;
}
