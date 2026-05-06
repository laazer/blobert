/**
 * Converts between store's flat key structure and typed ZoneTextureSettings objects.
 * Boundary layer that translates between two representations.
 */

import type {
  Zone,
  PatternFill,
  ColorFill,
  GradientFill,
  ImageFill,
  ZoneTextureSettings,
} from "../types/zoneTexture";
import { parseImageUvRect, stringifyImageUvRect } from "../components/ColorPicker/imageUvRect";

/**
 * Read a PatternFill from store values based on field prefix.
 * Field prefix examples: "pattern", "background"
 */
export function readPatternFillFromStore(
  zone: Zone,
  fieldPrefix: string,
  values: Readonly<Record<string, unknown>>
): PatternFill {
  const modeKey = `feat_${zone}_texture_${fieldPrefix}_mode`;
  const mode = (
    typeof values[modeKey] === "string" ? values[modeKey] : "single"
  ).toLowerCase();

  if (mode === "gradient") {
    return readGradientFill(zone, fieldPrefix, values);
  } else if (mode === "image") {
    return readImageFill(zone, fieldPrefix, values);
  } else {
    return readColorFill(zone, fieldPrefix, values);
  }
}

function readColorFill(
  zone: Zone,
  fieldPrefix: string,
  values: Readonly<Record<string, unknown>>
): ColorFill {
  const hexKey = `feat_${zone}_texture_${fieldPrefix}_hex`;
  const hex = typeof values[hexKey] === "string" ? values[hexKey] : "";
  return { type: "color", hex };
}

function readGradientFill(
  zone: Zone,
  fieldPrefix: string,
  values: Readonly<Record<string, unknown>>
): GradientFill {
  const aKey = `feat_${zone}_texture_${fieldPrefix}_grad_a`;
  const bKey = `feat_${zone}_texture_${fieldPrefix}_grad_b`;
  const dirKey = `feat_${zone}_texture_${fieldPrefix}_grad_direction`;

  const hex_a = typeof values[aKey] === "string" ? values[aKey] : "";
  const hex_b = typeof values[bKey] === "string" ? values[bKey] : "";
  const dir = typeof values[dirKey] === "string" ? values[dirKey] : "horizontal";

  return {
    type: "gradient",
    hex_a,
    hex_b,
    direction: (
      ["horizontal", "vertical", "radial"].includes(dir) ? dir : "horizontal"
    ) as "horizontal" | "vertical" | "radial",
  };
}

function readImageFill(
  zone: Zone,
  fieldPrefix: string,
  values: Readonly<Record<string, unknown>>
): ImageFill {
  const idKey = `feat_${zone}_texture_${fieldPrefix}_image_id`;
  const uvKey = `feat_${zone}_texture_${fieldPrefix}_image_uv_rect`;

  const asset_id = typeof values[idKey] === "string" ? values[idKey] : "";
  const uv_rect = parseImageUvRect(values[uvKey]);

  return {
    type: "image",
    asset_id,
    ...(uv_rect && { uv_rect }),
  };
}

/**
 * Read ZoneTextureSettings from store values.
 */
export function readZoneTextureSettingsFromStore(
  zone: Zone,
  values: Readonly<Record<string, unknown>>
): ZoneTextureSettings {
  const textureModeKey = `feat_${zone}_texture_mode`;
  const textureMode = (
    typeof values[textureModeKey] === "string" ? values[textureModeKey] : "none"
  ).toLowerCase();

  const background = readPatternFillFromStore(zone, "background", values);

  if (textureMode === "none") {
    return {
      zone,
      textureMode: "none",
      background,
    };
  }

  const pattern = readPatternFillFromStore(zone, "pattern", values);

  return {
    zone,
    textureMode: textureMode as "spots" | "stripes" | "checkerboard" | "assets",
    pattern,
    background,
  };
}

/**
 * Write PatternFill to store values.
 */
export function writePatternFillToStore(
  zone: Zone,
  fieldPrefix: string,
  fill: PatternFill
): Record<string, unknown> {
  const updates: Record<string, unknown> = {};

  const modeKey = `feat_${zone}_texture_${fieldPrefix}_mode`;
  updates[modeKey] = fill.type === "color" ? "single" : fill.type;

  if (fill.type === "color") {
    const hexKey = `feat_${zone}_texture_${fieldPrefix}_hex`;
    updates[hexKey] = fill.hex;
    // Clear other mode keys
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_a`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_b`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_direction`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_image_id`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_image_uv_rect`] = "";
  } else if (fill.type === "gradient") {
    const aKey = `feat_${zone}_texture_${fieldPrefix}_grad_a`;
    const bKey = `feat_${zone}_texture_${fieldPrefix}_grad_b`;
    const dirKey = `feat_${zone}_texture_${fieldPrefix}_grad_direction`;
    updates[aKey] = fill.hex_a;
    updates[bKey] = fill.hex_b;
    updates[dirKey] = fill.direction;
    // Clear other mode keys
    updates[`feat_${zone}_texture_${fieldPrefix}_hex`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_image_id`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_image_uv_rect`] = "";
  } else if (fill.type === "image") {
    const idKey = `feat_${zone}_texture_${fieldPrefix}_image_id`;
    const uvKey = `feat_${zone}_texture_${fieldPrefix}_image_uv_rect`;
    updates[idKey] = fill.asset_id;
    updates[uvKey] = fill.uv_rect ? stringifyImageUvRect(fill.uv_rect) : "";
    // Clear other mode keys
    updates[`feat_${zone}_texture_${fieldPrefix}_hex`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_a`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_b`] = "";
    updates[`feat_${zone}_texture_${fieldPrefix}_grad_direction`] = "";
  }

  return updates;
}

/**
 * Write ZoneTextureSettings to store values.
 */
export function writeZoneTextureSettingsToStore(
  settings: ZoneTextureSettings
): Record<string, unknown> {
  const updates: Record<string, unknown> = {};

  const textureModeKey = `feat_${settings.zone}_texture_mode`;
  updates[textureModeKey] = settings.textureMode;

  // Always write background
  const bgUpdates = writePatternFillToStore(
    settings.zone,
    "background",
    settings.background
  );
  Object.assign(updates, bgUpdates);

  // Write pattern only if it exists
  if (settings.textureMode !== "none" && settings.pattern) {
    const patternUpdates = writePatternFillToStore(
      settings.zone,
      "pattern",
      settings.pattern
    );
    Object.assign(updates, patternUpdates);
  } else {
    // Clear pattern keys if mode is "none"
    updates[`feat_${settings.zone}_texture_pattern_mode`] = "";
    updates[`feat_${settings.zone}_texture_pattern_hex`] = "";
    updates[`feat_${settings.zone}_texture_pattern_grad_a`] = "";
    updates[`feat_${settings.zone}_texture_pattern_grad_b`] = "";
    updates[`feat_${settings.zone}_texture_pattern_grad_direction`] = "";
    updates[`feat_${settings.zone}_texture_pattern_image_id`] = "";
    updates[`feat_${settings.zone}_texture_pattern_image_uv_rect`] = "";
  }

  return updates;
}
