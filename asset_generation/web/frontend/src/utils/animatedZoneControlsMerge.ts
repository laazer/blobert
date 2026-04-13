import type { AnimatedBuildControlDef } from "../types";
import { ZONE_FINISH_HEX_RE } from "../components/Preview/featureMaterialPartition";
import { normalizeAnimatedSlug } from "./enemyDisplay";

/** Aligned with ``asset_generation/python/src/utils/animated_build_options._FEATURE_ZONES_BY_SLUG``. */
export const FEATURE_ZONES_BY_SLUG: Readonly<Record<string, readonly string[]>> = {
  imp: ["body", "head", "limbs", "joints", "extra"],
  carapace_husk: ["body", "head", "limbs", "joints", "extra"],
  spider: ["body", "head", "limbs", "joints", "extra"],
  claw_crawler: ["body", "head", "limbs", "extra"],
  spitter: ["body", "head", "limbs"],
  slug: ["body", "head", "extra"],
};

/** Aligned with ``_FINISH_OPTIONS_ORDER`` in animated_build_options.py. */
export const FINISH_OPTIONS_ORDER = ["default", "glossy", "matte", "metallic", "gel"] as const;

const EXTRA_KINDS_SYNTHETIC = ["none", "shell", "spikes", "horns", "bulbs"] as const;
const SPIKE_SHAPES = ["cone", "pyramid"] as const;

function titleZone(zone: string): string {
  return zone
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

export function syntheticZoneControl(zone: string, field: "finish" | "hex"): AnimatedBuildControlDef {
  const labelBase = titleZone(zone);
  if (field === "finish") {
    return {
      key: `feat_${zone}_${field}`,
      label: `${labelBase} finish`,
      type: "select_str",
      options: [...FINISH_OPTIONS_ORDER],
      default: "default",
    };
  }
  return {
    key: `feat_${zone}_${field}`,
    label: `${labelBase} hex`,
    type: "str",
    default: "",
  };
}

/** Mirrors Python ``_zone_extra_control_defs`` for offline / partial API responses. */
export function syntheticExtraZoneDefsForSlug(slug: string): AnimatedBuildControlDef[] {
  const slugKey = normalizeAnimatedSlug(slug);
  const zones = FEATURE_ZONES_BY_SLUG[slugKey];
  if (!zones?.length) return [];
  const out: AnimatedBuildControlDef[] = [];
  for (const zone of zones) {
    const zlabel = titleZone(zone);
    out.push({
      key: `extra_zone_${zone}_kind`,
      label: `${zlabel} geometry extra`,
      type: "select_str",
      options: [...EXTRA_KINDS_SYNTHETIC],
      default: "none",
    });
    out.push({
      key: `extra_zone_${zone}_spike_shape`,
      label: `${zlabel} spike shape`,
      type: "select_str",
      options: [...SPIKE_SHAPES],
      default: "cone",
    });
    out.push({
      key: `extra_zone_${zone}_spike_count`,
      label: `${zlabel} spike count`,
      type: "int",
      min: 1,
      max: 24,
      default: 8,
    });
    out.push({
      key: `extra_zone_${zone}_spike_size`,
      label: `${zlabel} spike / horn size`,
      type: "float",
      min: 0.25,
      max: 3,
      step: 0.05,
      default: 1,
      unit: "× zone",
      hint: "Scales spike or horn geometry relative to the zone mesh size.",
    });
    out.push({
      key: `extra_zone_${zone}_bulb_count`,
      label: `${zlabel} bulb count`,
      type: "int",
      min: 1,
      max: 16,
      default: 4,
    });
    out.push({
      key: `extra_zone_${zone}_bulb_size`,
      label: `${zlabel} bulb size`,
      type: "float",
      min: 0.25,
      max: 3,
      step: 0.05,
      default: 1,
      unit: "× zone",
      hint: "Scales bulb geometry relative to the zone mesh size.",
    });
    out.push({
      key: `extra_zone_${zone}_clustering`,
      label: `${zlabel} extra clustering`,
      type: "float",
      min: 0,
      max: 1,
      step: 0.05,
      default: 0.5,
      unit: "0–1",
      hint: "For uniform placement, how tightly extras cluster on the zone surface.",
    });
    out.push({
      key: `extra_zone_${zone}_distribution`,
      label: `${zlabel} extra distribution`,
      type: "select_str",
      options: ["uniform", "random"],
      default: "uniform",
      segmented: true,
    });
    out.push({
      key: `extra_zone_${zone}_uniform_shape`,
      label: `${zlabel} uniform pattern`,
      type: "select_str",
      options: ["arc", "ring"],
      default: "arc",
    });
    for (const [pk, plab] of [
      ["place_top", "Top (+Z)"],
      ["place_bottom", "Bottom (−Z)"],
      ["place_front", "Front (+X)"],
      ["place_back", "Back (−X)"],
      ["place_right", "Right side (+Y)"],
      ["place_left", "Left side (−Y)"],
    ] as const) {
      out.push({
        key: `extra_zone_${zone}_${pk}`,
        label: `${zlabel} extra on ${plab}`,
        type: "bool",
        default: true,
      });
    }
    out.push({
      key: `extra_zone_${zone}_finish`,
      label: `${zlabel} extra finish`,
      type: "select_str",
      options: [...FINISH_OPTIONS_ORDER],
      default: "default",
    });
    out.push({
      key: `extra_zone_${zone}_hex`,
      label: `${zlabel} extra hex`,
      type: "str",
      default: "",
    });
  }
  return out;
}

/**
 * Ensures every coarse material zone for this slug appears in build controls even when the meta API
 * returns an older or partial list (e.g. only ``feat_body_*``). Preserves server defs when present;
 * inserts the canonical zone block before per-limb / per-joint rows.
 */
export function mergeCanonicalZoneControls(
  slug: string,
  defs: readonly AnimatedBuildControlDef[],
): AnimatedBuildControlDef[] {
  const slugKey = normalizeAnimatedSlug(slug);
  const zones = FEATURE_ZONES_BY_SLUG[slugKey];
  if (!zones?.length) {
    return [...defs];
  }

  const byKey = new Map(defs.map((d) => [d.key, d] as const));
  const withoutZones = defs.filter((d) => !ZONE_FINISH_HEX_RE.test(d.key));

  const canonicalZoneDefs: AnimatedBuildControlDef[] = [];
  for (const z of zones) {
    for (const field of ["finish", "hex"] as const) {
      const key = `feat_${z}_${field}`;
      canonicalZoneDefs.push(byKey.get(key) ?? syntheticZoneControl(z, field));
    }
  }

  const limbJointIdx = withoutZones.findIndex(
    (d) => d.key.startsWith("feat_limb_") || d.key.startsWith("feat_joint_"),
  );
  let merged: AnimatedBuildControlDef[];
  if (limbJointIdx >= 0) {
    merged = [...withoutZones.slice(0, limbJointIdx), ...canonicalZoneDefs, ...withoutZones.slice(limbJointIdx)];
  } else {
    merged = [...withoutZones, ...canonicalZoneDefs];
  }
  const seen = new Set(merged.map((d) => d.key));
  for (const d of syntheticExtraZoneDefsForSlug(slugKey)) {
    if (!seen.has(d.key)) {
      merged.push(d);
      seen.add(d.key);
    }
  }
  return merged;
}

/**
 * Merges API controls per slug and ensures listed slugs exist even when the meta response omits them
 * (e.g. ``animated_build_controls: {}`` on ImportError fallback or proxy misconfig).
 */
export function mergeCanonicalZoneControlsForAllSlugs(
  controls: Record<string, AnimatedBuildControlDef[]>,
  slugsToEnsure?: readonly string[],
): Record<string, AnimatedBuildControlDef[]> {
  const out: Record<string, AnimatedBuildControlDef[]> = {};
  for (const [slug, defs] of Object.entries(controls)) {
    const key = normalizeAnimatedSlug(slug);
    out[key] = mergeCanonicalZoneControls(slug, defs ?? []);
  }
  for (const slug of slugsToEnsure ?? []) {
    const key = normalizeAnimatedSlug(slug);
    if (!out[key]) {
      out[key] = mergeCanonicalZoneControls(slug, []);
    }
  }
  return out;
}
