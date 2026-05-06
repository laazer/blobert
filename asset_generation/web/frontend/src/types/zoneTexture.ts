/**
 * Domain types for zone texture configuration.
 * Replaces brittle string-based key manipulation with proper typed objects.
 * Ensures type-safe combinations via discriminated unions.
 */

import type { ImageUvRect } from "../components/ColorPicker/imageUvRect";

export type Zone = "body" | "head" | "limbs" | "joints" | "extra";

// Fill material types (union)
export type ColorFill = {
  type: "color";
  hex: string;
};

export type GradientFill = {
  type: "gradient";
  hex_a: string;
  hex_b: string;
  direction: "horizontal" | "vertical" | "radial";
};

export type ImageFill = {
  type: "image";
  asset_id: string;
  uv_rect?: ImageUvRect;
};

export type PatternFill = ColorFill | GradientFill | ImageFill;

// Zone texture settings with discriminated union ensuring valid combinations
export type ZoneTextureSettingsBase = {
  zone: Zone;
  background: PatternFill; // Always required
};

export type ZoneTextureSettings =
  | (ZoneTextureSettingsBase & {
      textureMode: "none";
      pattern?: undefined;
    })
  | (ZoneTextureSettingsBase & {
      textureMode: "spots" | "stripes" | "checkerboard" | "assets";
      pattern: PatternFill;
    });

/**
 * Type guard: check if pattern is defined
 */
export function hasPattern(
  settings: ZoneTextureSettings
): settings is ZoneTextureSettingsBase & {
  textureMode: "spots" | "stripes" | "checkerboard" | "assets";
  pattern: PatternFill;
} {
  return settings.textureMode !== "none" && settings.pattern !== undefined;
}

/**
 * Type guard: check if fill is a specific type
 */
export function isColorFill(fill: PatternFill): fill is ColorFill {
  return fill.type === "color";
}

export function isGradientFill(fill: PatternFill): fill is GradientFill {
  return fill.type === "gradient";
}

export function isImageFill(fill: PatternFill): fill is ImageFill {
  return fill.type === "image";
}
