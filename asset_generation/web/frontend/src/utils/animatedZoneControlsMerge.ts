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
  if (limbJointIdx >= 0) {
    return [...withoutZones.slice(0, limbJointIdx), ...canonicalZoneDefs, ...withoutZones.slice(limbJointIdx)];
  }
  return [...withoutZones, ...canonicalZoneDefs];
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
