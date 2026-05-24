import type { BuildControlDef } from "../types";
import {
  COARSE_ZONE_KEYS,
  type CoarseZoneKey,
} from "./elementColorPalettes";
import {
  zoneBackgroundColorKeys,
  zonePatternColorKeys,
} from "./zoneColorPickerBridge";

/** Build-option keys persisted as element default material state. */
export function coarseZoneElementDefaultKeys(zone: string): string[] {
  const bg = zoneBackgroundColorKeys(zone);
  const pattern = zonePatternColorKeys(zone, "pattern");
  const texBg = zonePatternColorKeys(zone, "background");
  const keys = [
    `feat_${zone}_finish`,
    `feat_${zone}_hex`,
    `feat_${zone}_texture_mode`,
    `feat_${zone}_color_mode`,
    bg.hexKey,
    bg.colorAKey,
    bg.colorBKey,
    bg.colorDirKey,
    bg.imageIdKey,
    bg.imagePreviewKey,
    bg.imageUvRectKey,
    `feat_${zone}_texture_background_mode`,
    texBg.hexKey,
    texBg.colorAKey,
    texBg.colorBKey,
    texBg.colorDirKey,
    texBg.imageIdKey,
    texBg.imagePreviewKey,
    texBg.imageUvRectKey,
    `feat_${zone}_texture_pattern_mode`,
    pattern.hexKey,
    pattern.colorAKey,
    pattern.colorBKey,
    pattern.colorDirKey,
    pattern.imageIdKey,
    pattern.imagePreviewKey,
    pattern.imageUvRectKey,
  ];
  if (pattern.legacySingleKey) keys.push(pattern.legacySingleKey);
  if (texBg.legacySingleKey) keys.push(texBg.legacySingleKey);
  return [...new Set(keys)];
}

export function allElementDefaultKeys(): string[] {
  const keys: string[] = [];
  for (const zone of COARSE_ZONE_KEYS) {
    keys.push(...coarseZoneElementDefaultKeys(zone));
  }
  return [...new Set(keys)];
}

export function pickElementMaterialOptions(
  values: Readonly<Record<string, unknown>>,
  knownDefKeys?: ReadonlySet<string>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of allElementDefaultKeys()) {
    if (knownDefKeys && !knownDefKeys.has(key)) continue;
    if (key in values) out[key] = values[key];
  }
  return out;
}

export function textureModeOptionsForZone(
  zone: CoarseZoneKey,
  defs: readonly BuildControlDef[],
): string[] {
  const def = defs.find((d) => d.key === `feat_${zone}_texture_mode`);
  if (def?.type === "select_str" && def.options.length > 0) {
    return def.options.map((o: string) => o.toLowerCase());
  }
  return ["none", "spots", "stripes", "checkerboard"];
}
