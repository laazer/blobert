/**
 * Pure helpers for splitting meta ``animated_build_controls`` rows into zone vs per-part material keys.
 * Used by ``FeatureMaterialControls`` and covered by unit tests (no DOM).
 */

const ZONE_ORDER = ["body", "head", "limbs", "joints", "extra"] as const;

/** Matches coarse zone finish/hex rows (not ``feat_limb_*`` / ``feat_joint_*``). */
export const ZONE_FINISH_HEX_RE = /^feat_(body|head|limbs|joints|extra)_(finish|hex)$/;

export function zoneRowRank(key: string): number {
  const m = /^feat_(\w+)_(finish|hex)$/.exec(key);
  if (!m) return 99;
  const z = m[1];
  const i = ZONE_ORDER.indexOf(z as (typeof ZONE_ORDER)[number]);
  return i >= 0 ? i * 2 + (m[2] === "finish" ? 0 : 1) : 50;
}

export function sortZoneFeatureDefs<T extends { key: string }>(defs: readonly T[]): T[] {
  return [...defs].sort((a, b) => zoneRowRank(a.key) - zoneRowRank(b.key));
}

export function partitionAnimatedFeatureDefs<T extends { key: string }>(
  allDefs: readonly T[],
): {
  featureDefs: T[];
  zoneDefs: T[];
  limbPartDefs: T[];
  jointPartDefs: T[];
} {
  const featureDefs = allDefs.filter((d) => d.key.startsWith("feat_"));
  const zoneDefs = sortZoneFeatureDefs(featureDefs.filter((d) => ZONE_FINISH_HEX_RE.test(d.key)));
  const limbPartDefs = featureDefs.filter((d) => d.key.startsWith("feat_limb_"));
  const jointPartDefs = featureDefs.filter((d) => d.key.startsWith("feat_joint_"));
  return { featureDefs, zoneDefs, limbPartDefs, jointPartDefs };
}
